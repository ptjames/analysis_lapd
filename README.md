# Analyzing LAPD Vehical Stop Data 
The following analysis is based on the dataset found [here](https://data.lacity.org/A-Safe-City/Vehicle-and-Pedestrian-Stop-Data-2010-to-Present/ci25-wgt7)

## Motivation
At the heart of this analysis is trying to understand whether police officers influence each others' policing behaviors. Specifically, this work investigates whether when a police officer works with other officers, does he/she incorporate the biases in how the other officers stop different demographics into his/her future policing.

## Problem Design
We can attempt to answer this question with the following design:

(insert image here)

At any point in time, we can calculate the distribution of how an officer stops demographics (sex or race/descent) over some time period. If we calculate this type of distribution at two different non-overlapping time periods (a "past period" and a "future period"), there will be some period in between that I will call the "influencing period". Let's assume action(s) can take place in the "influencing" period that will relate to an observable difference between the "past period" and "future period" distributions. The hypothesis here is that an officer making vehical stops with other officers, thereby working among officers with varying stops distributions, can be a kind of influencing action. For this problem design, the influencing officers' distributions are calculated during the "past period", so that they are comparable to the "past period" distribution of the officer being evaluated.  

### Notes
Regard stops demographic distributions: In the case of sex, this is a distribution over male and female, since the dataset only contains those labels. In the case of race / descent, we only include groups with more than 10k sample rows. Those include Hispanic/Latin/Mexican (H), Black (B), White (W), Other (O), Other Asian (A). 

Additionally, there are some assumptions made. It is possible that an officer changes which areas he/she operates in between "past period" and "future period". Different areas can have different demographic distributions, which can confound the design above. A rudimentary and non-perfect way I control for this by only considering cases where the distribution of an officer's reporting districts does not change too much, specifically only allow each district to change +/-10%. This can fail dramatically though, especially if an officer works in many different districts, each with a small percentage. Given the data we have to work with, a better sanity check for this is actually to perform our analysis on our sex stop distributions first. It is a reasonable assumption that the population distribution of M:F should not vary too much between districts. Therefore, the change in underlying population distribution is controlled for.

One final constraint involves how stop distributions are calculated. Just to ensure that vehical stops contributing to an officer's distribution truly reflect the actions of the officer being evaluated, and not his/her partner, we calculate our stop distributions only using vehical stops when an officer is alone / without another officer involved. 

## Process
First the vehical stop data was loaded into a database. This was done by:
1) [Define the stops table design](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/data/db_tables.py#L39)
2) [Load the stops csv into the database table](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/data/db_fill_from_csv.py#L61)

Next comes the analysis section. For anyone looking to dive deep into the code, start at the MAIN section [here](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L330) and scroll down from there. I have commented each step in the MAIN section to others can follow along. For those looking for a higher level overview, I have written out the following steps:

1) [Query the vehical stops data](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L52)
2) [Iterate over returned rows by date asc](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L350-L357)
    * [Gather data up until the next candidate "past period" reference date](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L368-L376)
    * [Remove any old data outside the "past period"](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L387-L388)
    * [Calculate officer demographic stop distributions in the "past period"](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L390-L397)
3) [Iterate over all gathered "past period" reference dates](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L418-L420)
  - 3a. [Determine the "influencing period"](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L422-L423)
  - 3b. [Iterate over each candidate officers](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L425-L429)
    - 3bi. [Gather the candidate officer's influencing officers in the "influencing period"](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L437-L442)
    - 3bii. [Calculate the weight distribution of the influencing officers](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L444-L453)
    - 3biii. [Store modeling data sample](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L455-L464)
4) [Iterate over each demographic](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L470-L472)
  - 4a. [Create train and evaluation datasets from step 3biii modeling data](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L475-L483)
  - 4b. [Train a Gradient Boosting classifier for the demographic](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L485-L486)
  - 4c. [Evaluate the model and create SHAP plots](https://github.com/ptjames/analysis_lapd/blob/a2b51f26fdf1461d38e705b7d16aa92e82bc16c3/analysis/analysis.py#L488-L492)

## Results
To analyze our results, we can make use of SHAP plots. For each demographic X, there are two SHAP plots constructed from our model predicting whether an officer's propensity to stop demographic X will increase/decrease. First, the summary plot shows the impact of each model feature on the output prediction. For each demographic X's summary plot, we are most concerned with the effect of the X_influencing feature, since this describes how our model relates policing behavior of an officer to the influence of other officers. Second, the dependence plot gives us a more detailed look into how X_influencing with X_officer_past jointly affects an officer's propensity to stop demographic X. For the first demographic analyzed, I will spend more time explaining the analysis process than subsequent demographics, since subsequent ones will follow a similar pattern.

### SHAP Female (F)
First it's importance the check whether our model has some degree of predictive power. This model's accuracy on our evaluation set comes out to 64.6%, on a set where our class 0 vs. class 1 split is 46.7% vs 53.3%. We should not expect 100% accuracy, since there are certainly other explanatory variables; however, an accuracy of 64.6% is definitely an improvement over the best naive guess of the majority class that would yield 53.3% accuracy. 

Regarding the summary plot, F_officer_past has the largest impact. This should be expected, since low F_officer_past values do not have too much room to go lower (likewise with high values going higher). F_influencing, however, does generally show that our prediction increases as influencing officers' propensity to stop demographic F increases, which is our initial hypothesis. 
![F SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/F_alone_shap_summary.png)

Diving a bit deeper, the dependence plot shows a key detail related to our hypothesis. Not all dots with low F_officer_past are treated the same. We can see that holding F_officer_past relatively constant, F_influencing still has a large effect on the SHAP value. The same can be said about dots with high F_officer_past not all be treated the same.
![F SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/F_alone_shap_dependence.png)

### SHAP Male (M)
The M model accuracy comes out to 65%, which is reasonably better than the naive guess at 54.5% accuracy. The SHAP summary plot generally shows that our prediction increases as M_influencing increases.
![M SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/M_alone_shap_summary.png)

Additionally, holding M_officer_past relatively constant, M_influencing still has a large effect on the SHAP value.
![M SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/M_alone_shap_dependence.png)

### SHAP Hispanic/Latin/Mexican (H)
Next we move onto racial demographics. Remember that we have to maintain stronger assumptions with these, since different areas of the city have different racial distributions. I will revisit this point one more time in the Future Work section below. 

Model accuracy for H comes out to 64.7%, which is an improvement over the naive guess at 56.5% accuracy. The SHAP summary plot generally shows that our prediction increases as H_influencing increases.
![H SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/H_alone_shap_summary.png)

For the dependence, holding H_officer_past relatively constant, H_influencing still has a large effect on the SHAP value.
![H SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/H_alone_shap_dependence.png)

### SHAP Black (B)
The B model accuracy comes out to 64.7%, which is a good deal better than the naive guess at 50.4% accuracy. The SHAP summary plot generally shows that our prediction increases as B_influencing increases.
![B SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/B_alone_shap_summary.png)

Additionally, holding B_officer_past relatively constant, B_influencing still has a large effect on the SHAP value. The B dependence plot also has a pretty interesting area at the far right where a group of red dots however close to a SHAP value of 0.0. This suggests a group of officers with a sustained propensity to stop black people at high rates. Note that it is possible this arises from operating in an area that is heavily black.
![B SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/B_alone_shap_dependence.png)

### SHAP White (W)
Model accuracy for W comes out to 62.1%, which is an improvement over the naive guess at 51.0% accuracy. The SHAP summary plot generally shows that our prediction increases as W_influencing increases.
![W SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/W_alone_shap_summary.png)

For the dependence, holding W_officer_past relatively constant, W_influencing still has a large effect on the SHAP value.
![W SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/W_alone_shap_dependence.png)

### SHAP Other (O)
For O, the model accuracy (60.6%) is not notably better than the naive guess (57.7%); therefore, it makes little sense to talk about the SHAP plots here. I've included links to them here for those interested.

[O SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/O_alone_shap_summary.png)

[O SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/O_alone_shap_dependence.png)

### SHAP Asian (A)
For A, the model accuracy (58.9%) is not notably better than the naive guess (53.9%); therefore, it makes little sense to talk about the SHAP plots here. I've included links to them here for those interested.

[A SHAP summary plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/A_alone_shap_summary.png)

[A SHAP dependence plot](https://github.com/ptjames/analysis_lapd/blob/master/analysis/plots/A_alone_shap_dependence.png)


## Future Work
From here, there are two clear improvements to make. First, a better way to control for population distributions in the areas officers are operating is needed. Factoring in reporting district demographic data along with the reporting districts offiers are making vehical stops in could better address this issue. Second, increasing sample size could both increase confidence in our models and increase model accuracy. The latter is possible learning more complex input -> output functions by using models requiring a larger number of trainable parameters. This sample size increase can come from expanding the dataset outside of LA county. Since this analysis project has shown promising results, I hope this improved analysis can be completed at some point.



