# Comprehensive RAG Testing Guide for Veterans Survey Data

## 1. Data Upload Instructions

1. **Save the CSV file:**
   - Copy the complete CSV data from the "Revised Veterans Survey Sample Data" artifact
   - Save it as `veterans_survey_data.csv` on your computer
   - Ensure all 88 records are included with complete fields

2. **Upload to your RAG system:**
   - Log in to your deployed PubSec-Info-Assistant instance
   - Upload the CSV file using the document upload functionality
   - Allow time for processing and indexing (usually 5-10 minutes)

3. **Verify successful upload:**
   - Check that the file appears in your document list
   - Confirm it's properly indexed by asking a simple test question: "How many comments mention wait time?"

## 2. Testing Categories and Questions

### CATEGORY A: Questions RAG Should Answer Successfully

These questions leverage RAG's strengths in retrieving and understanding text content.

#### A1. Specific Comment Retrieval

**Question:** "What was the comment about telehealth at Battle Creek VA Medical Center in February?"

**Expected Answer:** "The telehealth option saved me a long drive. The doctor was punctual for our video appointment and the technology worked flawlessly. Great alternative for routine follow-ups."

**Why RAG Should Succeed:** This is a straightforward retrieval task requiring only keyword matching and relevance ranking. The system needs to find comments containing "telehealth" and "Battle Creek" from February, which is explicit metadata in the dataset. The relevant record (comment_id: 22) should be easily retrieved based on these parameters.

**Your Observation:** 
[Record the actual RAG response here]

#### A2. Topic Identification

**Question:** "What topics are mentioned in relation to the PTSD program at Ann Arbor VA Medical Center?"

**Expected Answer:** The PTSD program at Ann Arbor is mentioned with topics including mental health, PTSD program, staff expertise, life-changing treatment, well-organized group sessions, and therapists experienced with veteran-specific issues.

**Why RAG Should Succeed:** This question requires identifying specific comments about a particular program at a specific facility, then extracting the associated topics. The information is explicitly stated in comments 31, 46, and 51, and the topic fields clearly list these concepts. This plays to RAG's strength in semantic search and information extraction.

**Your Observation:** 
[Record the actual RAG response here]

#### A3. Sentiment Analysis

**Question:** "What are the main complaints about the food at VA facilities based on the negative comments?"

**Expected Answer:** Complaints about food include: bland food, food being cold when delivered, terrible menu options, limited options not suitable for diabetics, and kitchen seeming to have limited food options. These issues were mentioned in inpatient stays across different facilities.

**Why RAG Should Succeed:** This requires finding comments with negative sentiment that mention food, which should be straightforward for the RAG system using a combination of metadata filtering (sentiment=Negative) and keyword search ("food"). The system can then extract and summarize the specific complaints, which is a core capability of generative AI.

**Your Observation:** 
[Record the actual RAG response here]

#### A4. Facility Comparison (Text-Based)

**Question:** "How do comments about technology differ between Battle Creek and Ann Arbor VA Medical Centers?"

**Expected Answer:** Both facilities receive positive comments about technology. Battle Creek comments mention telehealth options, electronic check-in, online prescription refills, and patient portals. Ann Arbor comments highlight check-in kiosks, telehealth systems, and the online tracking portal for benefits. Both facilities' veterans appreciate technology that saves time and increases convenience.

**Why RAG Should Succeed:** This requires semantic understanding to identify technology-related comments across two facilities and compare them. While it involves multiple dimensions, it's still primarily a text understanding task without complex calculations. The RAG system should be able to retrieve relevant comments and generate a comparative summary.

**Your Observation:** 
[Record the actual RAG response here]

#### A5. Pattern Recognition in Comments

**Question:** "What suggestions for improvement are mentioned by veterans in their comments?"

**Expected Answer:** Suggestions include: adding more disabled parking spaces, improving appointment scheduling systems, reducing wait times, increasing weekend staffing, better training for staff on policies, digitizing paperwork, creating more partnerships with local businesses for veteran employment, improving the discharge process, and enhancing the prescription refill process.

**Why RAG Should Succeed:** This leverages the language model's ability to identify implied suggestions within comments. While not explicitly labeled as "suggestions," the model can recognize phrases indicating desired improvements. This demonstrates RAG's strength in semantic understanding beyond simple keyword matching.

**Your Observation:** 
[Record the actual RAG response here]

### CATEGORY B: Questions Where RAG Will Likely Struggle

These questions test the limitations of RAG systems with numerical calculations and data aggregation.

#### B1. Retrieval Limitation Test

**Question:** "How many total survey responses are there for all facilities in the dataset?"

**Expected Answer:** 88 total survey responses (29 for Battle Creek, 30 for Ann Arbor, and 29 for Detroit)

**Why RAG Will Struggle:** This question reveals a fundamental limitation of RAG systems. When processing large datasets, RAG typically retrieves only a subset of relevant documents (often limited to top-k results based on similarity scoring). With default settings, it might only retrieve 3-5 documents, which means it will vastly undercount the total. This limitation directly impacts all aggregation questions because the system simply doesn't "see" all the relevant data.

**Your Observation:** 
[Record the actual RAG response here]

#### B2. Weekly Min/Max/Average Scores

**Question:** "What were the minimum, maximum, and average satisfaction scores for Battle Creek VA Medical Center during the first week of January 2025 (Jan 1-7)?"

**Expected Answer:** 
- Minimum: 2 (from comment_id: 2, Jan 2)
- Maximum: 5 (from comment_id: 4, Jan 4)
- Average: 3.2 (Sum of scores: 4+2+3+5+1 = 15, divided by 5 = 3.0)

**Why RAG Will Struggle:** This question requires multiple steps that challenge RAG systems:
1. Filtering by date range (requiring datetime understanding)
2. Filtering by facility
3. Identifying min and max values across multiple records
4. Calculating an average 
The system must retrieve ALL relevant records within the date range, which is unlikely given retrieval limitations. Even small retrieval errors will lead to incorrect calculations.

**Your Observation:** 
[Record the actual RAG response here]

#### B3. Monthly Facility Comparison

**Question:** "Compare the average satisfaction scores for Outpatient services between all three facilities for January 2025."

**Expected Answer:**
- Battle Creek: 3.29 (Sum of scores: 4+2+3+5+2+3+4 = 23, divided by 7 = 3.29)
- Ann Arbor: 3.29 (Sum of scores: 5+1+4+4+2+3+4 = 23, divided by 7 = 3.29)
- Detroit: 3.14 (Sum of scores: 1+5+3+2+4+3+4 = 22, divided by 7 = 3.14)
- Conclusion: All three facilities had similar average satisfaction scores for Outpatient services in January, with Battle Creek and Ann Arbor slightly higher than Detroit.

**Why RAG Will Struggle:** This requires filtering by month, survey type, and facility, then performing calculations for each group. The system needs to:
1. Correctly identify all January records for each facility
2. Filter for only Outpatient service types
3. Calculate three separate averages
4. Compare the results
Multiple calculation steps combined with retrieval limitations make this type of comparison particularly challenging for RAG systems.

**Your Observation:** 
[Record the actual RAG response here]

#### B4. Quarterly Min/Max by Survey Type

**Question:** "What were the minimum and maximum trust scores for Inpatient services at each facility during Q1 2025?"

**Expected Answer:**
- Battle Creek:
  - Minimum: 1 (from comment_id: 59)
  - Maximum: 5 (from comment_id: 58)
- Ann Arbor:
  - Minimum: 1 (from comment_id: 65)
  - Maximum: 5 (from comment_id: 62)
- Detroit:
  - Minimum: 2 (from comments 67 and 70)
  - Maximum: 5 (from comments 66 and 69)

**Why RAG Will Struggle:** This question combines multiple challenging aspects:
1. Filtering by quarter (requiring date range understanding)
2. Filtering by survey type
3. Grouping by facility
4. Finding min/max values for each group
The system would need to correctly retrieve and analyze all 13 inpatient records, which is unlikely given retrieval limitations. Additionally, comparing across multiple facilities adds complexity.

**Your Observation:** 
[Record the actual RAG response here]

#### B5. Trend Analysis Over Time

**Question:** "How did the average satisfaction scores for Outpatient services at Detroit VA Medical Center change from January to March 2025?"

**Expected Answer:**
- January: 3.14 (Sum: 1+5+3+2+4+3+4 = 22, Count: 7, Average: 3.14)
- February: 3.29 (Sum: 1+5+3+2+4+4 = 19, Count: 6, Average: 3.17)
- March: 3.5 (Sum: 5+3+3+4+2+4 = 21, Count: 6, Average: 3.5)
- Trend: Gradual improvement in satisfaction scores across the quarter, with March showing the highest average satisfaction.

**Why RAG Will Struggle:** This question requires:
1. Filtering by facility and service type
2. Grouping by month
3. Calculating averages for each month
4. Identifying the trend direction
The time-series aspect makes this particularly difficult for RAG systems, as they typically don't maintain context about trends across multiple calculation steps. The system would need to correctly retrieve all 19 relevant records and perform three separate calculations, which is unlikely.

**Your Observation:** 
[Record the actual RAG response here]

#### B6. Cross-Dimensional Analysis

**Question:** "What's the correlation between trust scores and satisfaction scores for Outpatient services across all facilities?"

**Expected Answer:** There is a strong positive correlation (approximately 0.94) between trust scores and satisfaction scores for Outpatient services. When trust scores are high, satisfaction scores are typically high as well, and vice versa.

**Why RAG Will Struggle:** This question requires statistical analysis that RAG systems are simply not designed to perform:
1. Calculating a correlation coefficient requires a specific mathematical formula
2. The system would need to retrieve ALL pairs of trust and satisfaction scores (which is unlikely given retrieval limitations)
3. Even with all the data, RAG systems don't have built-in statistical functions to compute correlations
This type of analysis is far beyond what typical RAG implementations can handle reliably.

**Your Observation:** 
[Record the actual RAG response here]

## 3. Testing the Pre-Computation Solution

After testing the questions above and documenting the limitations, you can demonstrate how pre-computation improves results:

1. **Create a pre-computed statistics document:**
   - Create a text file with calculated statistics like:
   ```
   Battle Creek VA Medical Center Statistics:
   - Total survey responses: 29
   - Outpatient responses by month: January (7), February (7), March (7)
   - Monthly average satisfaction scores (Outpatient): January (3.29), February (3.14), March (3.29)
   - Weekly min/max satisfaction scores (first week of January): Min (2), Max (5), Average (3.0)
   ...
   ```

2. **Upload this document alongside your raw data**

3. **Test the same questions again:**
   - Ask questions B2-B5 again
   - Document if the system can now retrieve and report the pre-computed statistics

## 4. Summary and Observations

After completing your testing, use this section to document key findings:

1. **Retrieval Limitations:**
   - Did the system consistently retrieve all relevant records for questions?
   - At what point did comprehensive retrieval break down?

2. **Calculation Accuracy:**
   - How accurate were simple calculations?
   - How accurate were complex multi-step calculations?

3. **Pre-computation Effectiveness:**
   - Did pre-computed statistics improve accuracy?
   - What types of questions still posed challenges even with pre-computation?

4. **Recommendations for Implementation:**
   - Which types of questions should rely on RAG?
   - Which types should use traditional analytics?
   - What pre-computed statistics would be most valuable?
