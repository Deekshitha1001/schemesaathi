# Data verification checklist

_Generated from `backend/data/schemes.json` by `backend/scripts/make_verification_checklist.py`. Do not edit by hand; edit the data and regenerate._

**Progress: 0 of 12 schemes verified.** The app shows a "demo data" warning until all 12 are done.

For each scheme: open the official page, tick every item, fix `schemes.json` wherever it differs, then run
`python scripts/mark_verified.py <scheme_id> --date YYYY-MM-DD`.

## PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)  (`pm_kisan`) — NOT verified

- Official page: https://pmkisan.gov.in
- Apply link in the app: https://pmkisan.gov.in
- Check these facts:
  - [ ] Benefit amount and instalment pattern
  - [ ] Exclusion categories (income tax payers, government employees, pensioners, institutional landholders)
  - [ ] Whether the landholding must be in your own name for the state
- Check the rules the app applies:
  - [ ] You or your family own cultivable agricultural land
  - [ ] You do not pay income tax
  - [ ] You are not a government employee
  - [ ] Documents list: aadhaar, bank_passbook, land_records, mobile_linked

## Ayushman Bharat PM-JAY (health cover)  (`pm_jay`) — NOT verified

- Official page: https://pmjay.gov.in
- Apply link in the app: https://beneficiary.nha.gov.in
- Check these facts:
  - [ ] Age-70 senior citizen rule and the cover amount for seniors
  - [ ] Family eligibility basis (SECC 2011 / state lists) and whether Karnataka runs its own health scheme alongside it
  - [ ] Cover amount per family
- Check the rules the app applies:
  - [ ] You are 70 or older, OR your family is on the government's list of eligible poor households (a BPL / Antyodaya card is only a rough indicator; the official check uses the SECC list)
  - [ ] Documents list: aadhaar, ration_card, age_proof, mobile_linked

## Atal Pension Yojana (APY)  (`apy`) — NOT verified

- Official page: https://www.jansuraksha.gov.in
- Apply link in the app: https://www.jansuraksha.gov.in
- Check these facts:
  - [ ] Entry age range 18-40
  - [ ] Income-tax-payer exclusion (introduced Oct 2022)
  - [ ] Pension amounts and contribution slabs
- Check the rules the app applies:
  - [ ] Your age is between 18 and 40
  - [ ] You have a savings bank account
  - [ ] You do not pay income tax (income tax payers cannot join)
  - [ ] Documents list: aadhaar, bank_passbook, mobile_linked, nominee_details

## PM Jeevan Jyoti Bima Yojana (life insurance)  (`pmjjby`) — NOT verified

- Official page: https://www.jansuraksha.gov.in
- Apply link in the app: https://www.jansuraksha.gov.in
- Already confirmed: 2026-10-30: premium (Rs 436), cover (Rs 2 lakh for death from any cause) and age band (18-50) confirmed against a PIB release dated May 2026 (static.pib.gov.in/WriteReadData/specificdocs/documents/2026/may/doc2026530879801.pdf). Cover-up-to-55 rule, auto-debit and how to apply are NOT yet confirmed, so the scheme stays unverified.
- Check these facts:
  - [ ] Premium (₹436) and cover (₹2 lakh)
  - [ ] Age limits (18-50 to join, cover up to 55)
- Check the rules the app applies:
  - [ ] Your age is between 18 and 50
  - [ ] You have a bank account
  - [ ] Documents list: aadhaar, bank_passbook, nominee_details

## PM Suraksha Bima Yojana (accident insurance)  (`pmsby`) — NOT verified

- Official page: https://www.jansuraksha.gov.in
- Apply link in the app: https://www.jansuraksha.gov.in
- Already confirmed: 2026-10-30: premium (Rs 20), cover (Rs 2 lakh for accidental death / permanent disability) and age band (18-70) confirmed against a PIB release dated May 2026 (static.pib.gov.in/WriteReadData/specificdocs/documents/2026/may/doc2026530879801.pdf). Partial-disability cover and how to apply are NOT yet confirmed, so the scheme stays unverified.
- Check these facts:
  - [ ] Premium (₹20) and cover amounts
  - [ ] Age limits (18-70)
- Check the rules the app applies:
  - [ ] Your age is between 18 and 70
  - [ ] You have a bank account
  - [ ] Documents list: aadhaar, bank_passbook, nominee_details

## PM Ujjwala Yojana (free LPG connection)  (`pmuy`) — NOT verified

- Official page: https://www.pmuy.gov.in
- Apply link in the app: https://www.pmuy.gov.in
- Check these facts:
  - [ ] Eligible categories (BPL, SC/ST, PMAY, Antyodaya, etc.)
  - [ ] Current financial support per connection
- Check the rules the app applies:
  - [ ] The applicant is a woman
  - [ ] The applicant is 18 or older
  - [ ] The household is poor / on a BPL-type list (BPL or Antyodaya card is a rough indicator; other categories also qualify)
  - [ ] Your household has no LPG connection yet
  - [ ] Documents list: aadhaar, bpl_proof, bank_passbook, lpg_declaration, passport_photo

## PM Awas Yojana (housing)  (`pmay`) — NOT verified

- Official page: https://pmaymis.gov.in
- Apply link in the app: https://pmaymis.gov.in
- Check these facts:
  - [ ] Current scheme version and portal (PMAY-G and PMAY-Urban 2.0)
  - [ ] Income bands (EWS / LIG / MIG) and subsidy details
  - [ ] Rural selection process
- Check the rules the app applies:
  - [ ] Your family does not own a pucca house
  - [ ] Household income is within the scheme limits (up to ₹18 lakh a year in urban categories; rural help depends on the government's beneficiary list)
  - [ ] Documents list: aadhaar, bank_passbook, income_certificate, house_declaration, residence_proof

## Sukanya Samriddhi Yojana (savings for a girl child)  (`ssy`) — NOT verified

- Official page: https://www.indiapost.gov.in
- Apply link in the app: https://www.indiapost.gov.in
- Check these facts:
  - [ ] Deposit limits
  - [ ] Maturity and withdrawal rules
  - [ ] Maximum two accounts per family (with exceptions)
  - [ ] Current interest rate (changes every quarter)
- Check the rules the app applies:
  - [ ] You have a daughter below 10 years of age (the account is opened in her name)
  - [ ] Documents list: girl_birth_cert, parent_id, aadhaar, passport_photo

## Indira Gandhi National Old Age Pension (NSAP)  (`ignoaps`) — NOT verified

- Official page: https://nsap.nic.in
- Apply link in the app: https://nsap.nic.in
- Check these facts:
  - [ ] Central pension amounts per age band
  - [ ] BPL requirement and state top-ups (Karnataka's own pension schemes may pay more)
- Check the rules the app applies:
  - [ ] You are 60 or older
  - [ ] Your household is on the state's BPL list (a BPL / Antyodaya card is a rough indicator)
  - [ ] Documents list: aadhaar, age_proof, bpl_proof, bank_passbook, passport_photo

## PM Mudra Yojana (small business loans)  (`mudra`) — NOT verified

- Official page: https://www.mudra.org.in
- Apply link in the app: https://www.mudra.org.in
- Check these facts:
  - [ ] Loan band limits and the Tarun Plus band
  - [ ] Whether new entrepreneurs without a running business qualify
- Check the rules the app applies:
  - [ ] You are 18 or older
  - [ ] You run (or want to start) a small non-farm business or craft
  - [ ] Documents list: aadhaar, business_proof, bank_passbook, passport_photo, residence_proof

## PM Vishwakarma (support for traditional artisans)  (`pm_vishwakarma`) — NOT verified

- Official page: https://pmvishwakarma.gov.in
- Apply link in the app: https://pmvishwakarma.gov.in
- Check these facts:
  - [ ] Exact list of the 18 trades (check whether handloom weaving is included)
  - [ ] Loan amounts and interest rate
  - [ ] Toolkit amount and training stipend
  - [ ] Restriction on people who recently took Mudra / PMEGP / SVANidhi loans
- Check the rules the app applies:
  - [ ] You work in one of the 18 listed traditional trades (carpenter, blacksmith, goldsmith, potter, sculptor, cobbler, mason, basket/mat/broom maker, toy maker, barber, garland maker, washerman, tailor, boat maker, armourer, hammer & toolkit maker, locksmith, fishing-net maker)
  - [ ] You are 18 or older
  - [ ] You are not a government employee
  - [ ] Documents list: aadhaar, mobile_linked, bank_passbook, trade_proof, ration_card

## Gruha Lakshmi (Karnataka)  (`gruha_lakshmi`) — NOT verified

- Official page: https://sevasindhu.karnataka.gov.in
- Apply link in the app: https://sevasindhu.karnataka.gov.in
- Check these facts:
  - [ ] Current enrolment status (the scheme may have closed or reopened registration)
  - [ ] Exclusion rules (income tax / GST payers)
  - [ ] Apply channels and amount
- Check the rules the app applies:
  - [ ] You live in Karnataka
  - [ ] The applicant is a woman
  - [ ] She is the woman head of the family
  - [ ] No one in the household pays income tax or GST
  - [ ] The family has a ration card (BPL, Antyodaya or APL)
  - [ ] Documents list: aadhaar, ration_card, bank_passbook, mobile_linked

## Also have a native speaker review

- [ ] Hindi text in `data/schemes.json`, `data/documents.json`, `app/fields.py` and `frontend/src/i18n.js`
- [ ] Kannada text in the same four files
