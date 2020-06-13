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

## Code Walkthrough
Explain here

## Results
Results here

## Future Work
Future work here



