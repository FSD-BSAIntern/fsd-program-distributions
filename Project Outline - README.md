### Original Prompt:



Help me build an app in visual studio code that takes three inputs: x1 is a specific region or list or regions or agency or list of agencies "ex IN for inland, S for south, or just Jewish Family Services". x2 is a selection to view the data at a week to week level, month to month level, or year over year level. X3 is a range or dates, or a selected date and then the selection of how many previous time periods (ex. the week of Feb. 16 and the previous 3 weeks).  x3.5 also has the option of comparing the selected range (if not in year over year view) to the previous years same dates. There should be 4 outputs in this calculator. Y1 is a summary table of the selected x1s, displaying lbs. distributed (by the selected x2 view), HH size, and then the raw delta of lbs. as well as the % delta of lbs.  compared to the selected x2 format. any +/- 20% change is highlighted in this table or otherwise marked (ex \*\*\*\*). Y2 is a bar + line graph for each selected x1 where the bar is the current year/wk./mo. and the line is the previous year if that option was selected. as with the table summary, any +/-20% change is highlighted. there should be a plot for each region or agency that was selected in x1. y3 is a verbal summary of the above statistics with particular attention to any highlighted outliers. y4 is a downloadable report of the previous outputs, in a clean and accessible format. Assume that the data I have is sufficient to accomplish this. My column names include, fiscal year, quarter, month, date, bill to agency, donated vs purchased, product type code, agency category, size (HH) code, gross weight distributed, zip code, geographical region code, city, etc. Additionally, each row in my dataset corresponds to a single order for a single agency, for one day. Please repeat back to me what the inputs and outputs of this report should be. Do not start coding yet, I want you to walk me through this process step by step and only move on when I prompt you to. Please ask any clarifying questions to collect additional context before proceeding. 



#### Clarifying Questions: 

1\. The app should not allow for the mixing of regions and agencies in the same report. Output will be exclusively at the agency level or region level per report that is run. 



2\. "Lbs. distributed" is defined by a sum of gross weight distributed per agency/region over the selected time period. Gross weight is the pounds of food that was delivered to the selected agency/region combination per each order.



3\. HH Size is both numeric and categorical, with some containing a flat number "ex. 225 or 90" or a string. For example "67D 130P" means 67 individuals received dry product, while 130 individuals received produce (130 includes the previous count of 67). The range of codes is quite wide (from 10 to 1000), and the goal is to create a sub-group to collapse the codes into standard categories (ex. Extra Small, Small, Medium, Large, Extra Large)



4\. Weekly grouping should be done starting with the Monday of each selected date. I.e. week one is 2/16 to 2/22. There are no fiscal weeks, but it is important to note that the fiscal year starts on the first of jul from the previous year. ex. FY 24 began on 7-01-23 and ends on 6-31-24.



5\. In YoY comparisons, previous year should refer to the previous fiscal year, as defined by the answer to question 4. 



6\. The baseline for deltas when x3.5 is off should be a comparison of the immediately previous period AND the average over the selected range. 





##### Inputs



X0 (mode selector). Report level must be one or the other per run:

* Region-level report (filter and output by geographical region code), or
* Agency-level report (filter and output by bill to agency)



X1 (entity selector). Depending on X0:

* If region-level: one region code or a list of region codes (e.g., IN, S)
* If agency-level: one agency name or a list of agencies (e.g., Jewish Family Services)



X2 (time aggregation). One of:

* Weekly (weeks run Monday–Sunday; e.g., 2/16–2/22)
* Monthly
* Yearly (fiscal year)



X3 (time window). 

* Either a date range (start–end), or
* An anchor date plus “previous N periods” where period = X2



X3.5 (prior fiscal-year same-dates comparison toggle).

* If X2 is weekly or monthly: optionally include comparison against the same dates in the previous fiscal year.
* If X2 is yearly: YoY is inherent (FY vs previous FY).



##### Outputs



Y1. Summary table, for each selected X1 entity and each period in the selected window:

* Lbs distributed = SUM(gross weight distributed)
* Household size category (collapsed bucket, e.g., XS/S/M/L/XL) and a chosen summary metric (to define in Step 1)
* Raw delta lbs vs:
* &nbsp;	a) immediately previous period, and
* &nbsp;	b) average over the selected range
* Percent delta lbs vs those same baselines
* Flag/highlight where abs(% delta) ≥ 20% (for each baseline comparison you choose to display)



Y2. One bar+line plot per selected X1 entity:

* Bars = current FY values across the selected periods
* Line (optional) = previous FY same-dates values if X3.5 is enabled
* Visual emphasis for periods with abs(% delta) ≥ 20% (same rule as table)



Y3. Verbal summary emphasizing:

* Overall trends
* Any abs(% delta) ≥ 20% outliers (and which baseline triggered them)
* Biggest increases/decreases



Y4. Downloadable report containing Y1, Y2, Y3 in a clean accessible format (PDF or HTML-to-PDF).



