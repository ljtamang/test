import re
import spacy

# Load spaCy model
try:
    nlp = spacy.load('en_core_web_trf')
except:
    nlp = spacy.load('en_core_web_sm')

# 1) Address patterns
ADDRESS_CONTEXT_PATTERN = r'(?i)\b(?:live[sd]? at|located at|reside[sd]? at|address is|moved to)\b[^.]*'
STREET_ADDRESS_PATTERN = r'\d{1,5}\s(?:[A-Z][a-z]*\.?\s?)+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Lane|Ln|Drive|Dr|Court|Ct|Way|Terrace|Ter|Place|Pl|Parkway|Pkwy|Circle|Cir|Loop|Sq)\b'
CITY_STATE_ZIP_PATTERN  = r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*,?\s[A-Z]{2}\s?\d{5}\b'


# 2) Phone
PHONE_PATTERN = r'''(?x)
    (?:\+?\d{1,3}[-.\s]?)?      # country code
    (?:\(?\d{3}\)?[-.\s]?)      # area code
    \d{3}[-.\s]?\d{4}           # local number
'''


# All supported DOB-related keywords
DOB_KEYWORDS = r'''
    (?:
        \b(?:DOB|D\.O\.B\.?|birth\s+date|date\s+of\s+birth|
        my\s+date\s+of\s+birth\s+is|date\s+of\s+birth\s+is|
        was\s+born\s+on|born\s+on|born)\b
    )
    [\s:;,\-()]*  # Possible separators
'''

# Flexible date patterns including various common formats
FLEXIBLE_DATE_PATTERN = r'''
    (?:
        (?:\d{1,2}[/\-. ]\d{1,2}[/\-. ]\d{2,4}) |                          # 12/05/1995, 12-05-1995
        (?:\d{4}[/\-. ]\d{1,2}[/\-. ]\d{1,2}) |                          # 1995-05-12
        (?:\d{1,2}(?:st|nd|rd|th)?[\s\-.,]*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,.-]*\d{0,4}) |
        (?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-.,]*\d{1,2}(?:st|nd|rd|th)?(?:[\s,.-]*\d{0,4})?) |
        (?:\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-.,]+\d{4}) |
        (?:\d{1,2}[\s\-.,]*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)
        | 
       (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?
        |May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?
        |Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)              # Month name
       \s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})? 
       | 
       \d{1,2}(?:st|nd|rd|th)?\s+
       (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?
        |May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?
        |Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)
       [\s,.-]*\d{4}  
    )
'''

# Final pattern with global flags at the start
DOB_FULL_PATTERN = rf'''(?ix)
    {DOB_KEYWORDS}
    \(?{FLEXIBLE_DATE_PATTERN}\)?
'''

# Preprocessing function to clean text
def clean_text(text: str) -> str:
    # Normalize whitespace and remove stray symbols
    text = re.sub(r'\s+', ' ', text)               # collapse multiple spaces
    text = re.sub(r'[^\w\s:/\-.()]', '', text)    # remove unwanted characters
    #text = re.sub(r'[^\w\s]', '', text)    # remove unwanted characters
    text = text.strip()
    return text


def redact_pii(text: str) -> str:
    # Address → Phone → DOB
    text=clean_text(text)
    for pat in (ADDRESS_CONTEXT_PATTERN, STREET_ADDRESS_PATTERN, CITY_STATE_ZIP_PATTERN):
        text = re.sub(pat, '[REDACTED ADDRESS]', text)

    text = re.sub(PHONE_PATTERN, '[REDACTED PHONE]', text)
    text = re.sub(DOB_FULL_PATTERN, '[REDACTED DOB]', text)

    # Finally, catch any remaining location mentions (city/GPE/etc.)
    doc = nlp(text)
    spans = []
    for ent in doc.ents:
        if ent.label_ in ('GPE', 'LOC', 'FAC'):
            spans.append((ent.start_char, ent.end_char))
    for start, end in sorted(spans, key=lambda x: x[0], reverse=True):
        text = text[:start] + '[REDACTED ADDRESS]' + text[end:]
    return text

# ----------------------------
# Quick sanity‑check on examples
# ----------------------------
if __name__ == '__main__':
    examples = [
         "My name is Michael Anderson, DOB 08/14/1970, residing at 432 Veterans Memorial Drive, Portland, OR 97201. You can reach me at manderson@outlook.com or call my cell at (503) 555-7654. My SSN is 890-12-3456.",
"This is Jennifer Thompson (SSN ending in 4567) requesting assistance with my benefits. I recently moved from 765 Freedom Court, Apt 3D, Houston, TX 77002 to a new address. Please update your records and contact me at jennifer.thompson@gmail.com or 713-555-8765. My date of birth is 09/23/1985 and my driver's license is TX-12345678.",
"To Whom It May Concern: I am William Roberts, a Vietnam veteran (DOB: 05/12/1952). I'm having issues with charges on my Visa card ending in 3456. Please contact me at 543 Liberty Square, Philadelphia, Pennsylvania 19103 or call 215.555.9876. For verification, the last 4 of my SSN are 5678 and my PA driver's license number is 12345678.",
"Feedback from Patricia Garcia: I visited the clinic on March 3rd. My contact details are pgarcia1977@yahoo.com, phone (305) 555-0123, address 876 Stars & Stripes Blvd, Miami, FL 33130. For records: DOB 06/19/1977, SSN 123-45-6789, DL# FL-G123-456-78-910-0. There was an unauthorized charge of $50 to my Mastercard 5412-7890-1234-5678.",
"This is feedback from Richard Lee Wilson Jr. (Born November 30, 1968, Social Security Number ends with 7890). I have concerns about my recent appointment. My current address is P.O. Box 4567, New York, NY 10001. You can contact me at richard.wilson@hotmail.com or (212) 555-2345. My New York DL is WILSON123456 and there's an issue with my Amex card (3765 123456 78901).",
"Hello, I'm Katherine Martinez (SSN: 345-67-8901) writing about my experience at the San Diego VA. I've recently relocated to 159 Ocean View Terrace, San Diego, CA 92101 from my previous address in Florida. My phone number is (619) 555-4321, email is k.martinez@icloud.com, and I was born on 07/04/1982. My California driver's license (A9876543) was just issued last month. Please update my payment method to my new Discover card 6011-2233-4455-6677.",
"Feedback submitted by James T. Walker, retired Army Sergeant. Contact info: 472 Mountain View Road, Denver, Colorado 80202, jtwalker@gmail.com, cell: 303-555-6789. Personal details for verification: DOB - 10/18/1979, last four of social - 3412, Colorado DL #987654321. The VA hospital charged my Visa 4111-2222-3333-4444 for services that should have been covered by my benefits."

    ]

    for i, ex in enumerate(examples, 1):
        print(f"\n--- Example {i} ---")
        print(redact_pii(ex))
