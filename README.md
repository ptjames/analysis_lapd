# Analyzing LAPD Vehical Stop Data 
The dataset on LAPD vehicle and pedestrian stops can be found [here](https://data.lacity.org/A-Safe-City/Vehicle-and-Pedestrian-Stop-Data-2010-to-Present/ci25-wgt7)

## Motivation
At the heart of this analysis is exploring whether police officers influence each others' policing behaviors. Specifically, when a police officer makes vehicle stops with other officers, does he/she incorporate biases in how the other officers stop various demographics into his/her policing.

## Problem Design
We can attempt to answer this question with the design below.

![problem_design](https://github.com/ptjames/analysis_lapd/blob/master/analysis/problem_design.jpg)

At any point in time, we can calculate the distribution of demographics (sex or race/descent) for how an officer stops vehicles over some time period. If we calculate this type of distribution at two non-overlapping time periods ("past period" and "future period" in the graphic), there will be a period in between; call this the "influencing period". Assume action(s) can take place in the "influencing" period that will result in an observable difference between an officer's "past period" and "future period" distributions. The hypothesis here is that when an officer makes vehicle stops with other officers during the "influencing period", the higher the likelihood influencing officers stopped a specific demographic during the "past period", the more likely the original officer will stop that demographic in the "future period". To approximate this relationship, a model will be trained to predict whether an officer's probability of stopping a demographic will increase or not increase between "past period" and "future period". This is formatted as a binary problem with class 1 being an increase and class 0 otherwise. The model input features include:

 * Set X_officer_past: for each demographic X, an officer's probability of stopping X in "past period"
 * Set X_influencing: for each demographic X, the influencing officers' weighted probability of stopping X in "past period"

### Assumptions
It is possible that an officer changes which areas he/she operates in between "past period" and "future period". Different areas can have different demographic distributions, which could confound the design above. A rudimentary and non-perfect way I control for this is by only considering model training samples where the distribution of an officer's reporting districts does not vary too much between "past period" and "future period". "Too much" here is defined as a change of more than +/-0.1 in a reporting districts probability. This can fail dramatically though, especially if an officer works in many different districts, each with a small probability. To provide a better sanity check during the process, analysis is first performed for sex-based demographics. It is a reasonable assumption that the population distribution of M:F should not vary too much between districts. Therefore, the change in underlying population distribution is controlled for.

### Constraints
Regarding demographics considered: In the case of sex, male and female are considered, since the dataset only contains those labels. For race / descent, only groups with more than 10k sample rows are included. These include Hispanic/Latin/Mexican (H), Black (B), White (W), Other (O), Other Asian (A). 

To ensure that vehicle stops contributing to an officer's distribution of demographics truly reflect the actions of the officer being evaluated (and not his/her partner), we calculate our stop distributions only using vehicle stops when an officer is alone / without another officer involved. 

## Process
First the vehicle stop data was loaded into a database. A MySQL database was used, since the analysis does not require more complex SQL actions, but other variants of SQL would be fine. At a high level this process is as follows:
1) [Define the stops table design](https://github.com/ptjames/analysis_lapd/blob/master/data/db_tables.py#L43-L58)
2) [Load the stops csv into the table](https://github.com/ptjames/analysis_lapd/blob/master/data/db_fill_from_csv.py#L85-L104)

Next comes the analysis section. For anyone looking to dive deep into the code, start at the [MAIN section](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L330) and scroll down. I have commented each step in the MAIN section, so others can follow along. For those looking for a higher level overview, steps are as follows:

1) [Query the vehicle stops data](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L52)
2) [Iterate over returned rows by date asc](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L350-L357)
    * [Gather data up until the next candidate "past period" reference date](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L368-L376)
    * [Remove any old data outside the "past period"](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L387-L388)
    * [Calculate officer demographic stop distributions in the "past period"](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L390-L397)
3) [Iterate over all gathered "past period" reference dates](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L418-L420)
    * [Determine the "influencing period"](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L422-L423)
    * [Iterate over each candidate officers](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L425-L429)
        * [Gather the candidate officer's influencing officers in the "influencing period"](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L437-L442)
        * [Calculate the weighted distribution of the influencing officers](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L444-L453)
        * [Store modeling data sample](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L455-L464)
4) [Iterate over each demographic](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L470-L472)
    * [Create train and evaluation datasets from stored modeling data](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L475-L483)
    * [Train a Gradient Boosting classifier for the demographic](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L485-L486)
    * [Evaluate the model and create SHAP plots](https://github.com/ptjames/analysis_lapd/blob/master/analysis/analysis.py#L488-L492)

## Results
For this analysis, SHAP plots are used to interpret each model. In brief, a SHAP value shows to what degree an input feature contributes towards a prediction value (positive SHAP value means higher prediction value, etc). Each input data observation gets its own set of SHAP values. General information on SHAP values and plots can be found [here](https://github.com/slundberg/shap). For each demographic X, there are two SHAP plots constructed for each demographic's model. First, the summary SHAP plot shows the impact of each model feature on the output binary prediction. For each demographic X's summary plot, we focus on the effect of the X_influencing feature, since it describes how our model relates an officer's policing behavior to the influence of other officers. Second, the dependence SHAP plot gives us a more detailed look into how (X_influencing, X_officer_past) jointly affects an officer's propensity to stop demographic X. For the first demographic analyzed, a more thorough explanation is given than subsequent demographics, since subsequent ones will follow a similar analysis pattern.

### SHAP Female (F)
First it is important the check whether our model has some degree of predictive power. If a model performs poorly on an evaluation set, any learned feature-target relationships will not generalize outside the training set. The F model's accuracy on the evaluation set (which has a 46.7% vs 53.3% split for class 0 vs. class 1) comes out to 64.6%. Anywhere near 100% accuracy is not expected, since there are certainly other explanatory variables and stochasticity not included; however, an accuracy of 64.6% is definitely an improvement over the best naive guess of the majority class that would yield 53.3% accuracy. 

Regarding the summary plot, F_officer_past has the largest impact. This should be expected, since low F_officer_past values do not have too much room to go lower (likewise with high values going higher). F_influencing, however, does generally show that our prediction increases as influencing officers' propensities to stop demographic F increase, which is our initial hypothesis. 
![F SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/F_alone_shap_summary.png)

Diving a bit deeper, the dependence plot shows a key detail related to our hypothesis. Not all dots (each an input observation) with low F_officer_past are treated the same. We can see that when holding F_officer_past relatively constant, F_influencing still has a large effect on the SHAP value. The same can be said about dots with high F_officer_past (they are not all treated the same).
![F SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/F_alone_shap_dependence.png)

### SHAP Male (M)
The M model accuracy comes out to 65%, which is reasonably better than the naive guess at 54.5% accuracy. The SHAP summary plot generally shows that our prediction increases as M_influencing increases.
![M SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/M_alone_shap_summary.png)

Additionally, when holding M_officer_past relatively constant, M_influencing still has a large effect on the SHAP value.
![M SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/M_alone_shap_dependence.png)

### SHAP Hispanic/Latin/Mexican (H)
Next the plots for race-based demographics are examined. Remember that stronger assumptions are maintained for these, since different areas of the city have different racial distributions. I will revisit this point one more time in the Future Work section below. 

Model accuracy for H comes out to 64.7%, which is an improvement over the naive guess at 56.5% accuracy. The SHAP summary plot generally shows that our prediction increases as H_influencing increases.
![H SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/H_alone_shap_summary.png)

For the dependence, when holding H_officer_past relatively constant, H_influencing still has a large effect on the SHAP value.
![H SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/H_alone_shap_dependence.png)

### SHAP Black (B)
The B model accuracy comes out to 64.7%, which is a good deal better than the naive guess at 50.4% accuracy. The SHAP summary plot generally shows that our prediction increases as B_influencing increases.
![B SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/B_alone_shap_summary.png)

When holding B_officer_past relatively constant, B_influencing still has a large effect on the SHAP value. The B dependence plot also has an interesting area at the far right where a group of red dots hover close to a SHAP value of 0.0. This suggests a group of officers with a sustained propensity to stop black people at high rates. Note that it is possible this arises from operating in an area that is predominantly black.
![B SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/B_alone_shap_dependence.png)

### SHAP White (W)
Model accuracy for W comes out to 62.1%, which is an improvement over the naive guess at 51.0% accuracy. The SHAP summary plot generally shows that our prediction increases as W_influencing increases.
![W SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/W_alone_shap_summary.png)

For the dependence, when holding W_officer_past relatively constant, W_influencing still has a large effect on the SHAP value.
![W SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/W_alone_shap_dependence.png)

### SHAP Other (O)
For O, the model accuracy (60.6%) is not notably better than the naive guess (57.7%); therefore, it makes little sense to talk about the SHAP plots here. Links to the plots have been included for those interested.

 * [O SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/O_alone_shap_summary.png)
 * [O SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/O_alone_shap_dependence.png)

### SHAP Asian (A)
For A, the model accuracy (58.9%) is not notably better than the naive guess (53.9%); therefore, it makes little sense to talk about the SHAP plots here. Links to the plots have been included for those interested.

 * [A SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/A_alone_shap_summary.png)
 * [A SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/A_alone_shap_dependence.png)


## Future Work
From here, there are two clear improvements to make. First, a better way to control for area population distributions is needed. Factoring in reporting district demographic data along with the reporting districts where officers are making vehicle stops could better address this issue. Second, increasing sample size could both increase confidence in our models and increase model accuracy. The latter is possible by learning more complex input -> output functions through using models that require a larger number of trainable parameters (note, however, that increased model complexity does not guarantee improved performance). This sample size increase can come from expanding the dataset outside of LA county. Since this analysis has shown promising results, I hope these improvements can be completed at some point.



