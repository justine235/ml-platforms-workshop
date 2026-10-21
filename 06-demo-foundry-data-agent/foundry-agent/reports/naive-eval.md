# Eval report: naive

- Pass rate: 0.0%

## By type

| Type | Passed | Total |
| --- | ---: | ---: |
| agg | 0 | 10 |
| count | 0 | 5 |
| detail | 0 | 1 |
| guardrail | 0 | 1 |
| list | 0 | 6 |
| lookup | 0 | 1 |
| multi-hop | 0 | 2 |
| out_of_scope | 0 | 1 |
| unanswerable | 0 | 3 |

## By difficulty

| Difficulty | Passed | Total |
| --- | ---: | ---: |
| easy | 0 | 6 |
| hard | 0 | 10 |
| medium | 0 | 14 |

## Failures

- **Q01** How many equipment assets are registered in the ERP, and how many are Active, Retired and Disposed?: missing key: total
- **Q02** How many reconciliation exceptions are open in total, and how many are there per exception type?: missing key: total
- **Q03** How many CRIT fault episodes were never followed by a corrective work order within 7 days (data cutoff 2026-10-01)?: missing key: count
- **Q04** Which CMMS work orders are duplicates of another work order, and which work order does each one duplicate?: missing key: count
- **Q05** Which work orders were closed before they were opened (swapped timestamps in the CMMS)?: missing key: count
- **Q06** Which Retired or Disposed assets are still sending telemetry after their retirement date?: missing key: count
- **Q07** Which Active assets have a telematics device installed but sent nothing for more than 14 days, and which were never linked to any telemetry?: missing key: stopped_reporting
- **Q08** Which telematics devices cannot be linked to any ERP asset, and how many telemetry records did each of them send?: missing key: count
- **Q09** How many CMMS work orders carry an asset tag that matches nothing in the ERP, and how many distinct tags is that?: missing key: work_orders
- **Q10** Which site has the most CRIT fault episodes without a corrective work order?: missing key: count
- **Q11** What is the overall CRIT match rate - the share of judged CRIT fault episodes (matched plus unmatched, pending ones excluded) that have a corrective work order?: missing key: rate_percent
- **Q12** In which month was the CRIT match rate the lowest, and what was it?: missing key: month
- **Q13** At site FR-MRS-01 in 2026-04, how many CRIT fault episodes were there and what was the CRIT match rate?: missing key: crit_episodes
- **Q14** What is the median delay in hours between the first fault record of a matched CRIT episode and the opening of its corrective work order (negative = the work order came first)?: missing key: median_hours
- **Q15** Which equipment class had the most corrective work orders, and what was their total parts cost in EUR?: missing key: equipment_class
- **Q16** What are the top 3 sites by corrective-maintenance repair hours (sum of the durations of corrective work orders)?: missing key: sites
- **Q17** Which site opened the most corrective work orders in September 2026 (list every site if tied), and what was their parts cost?: missing key: sites
- **Q18** How many corrective work orders have no matching fault episode in the telemetry, and what are the reasons?: missing key: total
- **Q19** Among the matched CRIT fault episodes, how many had their corrective work order opened within 24 hours of the first fault record, and how many took more than 3 days?: missing key: within_24h
- **Q20** Why is asset EQ-00619 flagged in the reconciliation, and when did it last send telemetry?: missing key: asset
- **Q21** On the latest scoring date (2026-09-30), how many assets are in each failure-risk band, and which site has the most High-risk assets?: missing key: High
- **Q22** List the High-risk assets on 2026-09-30 with their site, equipment class, score and top drivers.: missing key: assets
- **Q23** Which equipment class has the highest share of its scored assets in the High risk band?: missing key: classes
- **Q24** For the 5 assets with the highest failure-risk score on 2026-09-30, how many corrective work orders were opened in the 90 days before 2026-10-01, and how many reconciliation exceptions does each have?: missing key: assets
- **Q25** Which High-risk assets also have a CRIT fault episode that is still waiting for a corrective work order (reconciliation status PENDING)?: missing key: count
- **Q26** What was the fuel cost per site in September 2026?: expected refusal or unanswerable result
- **Q27** Which operator was driving the machine when each CRIT fault occurred?: expected refusal or unanswerable result
- **Q28** How many safety incidents happened at ES-MAD-01 this year?: expected refusal or unanswerable result
- **Q29** What will the failure risk of EQ-02893 be on 2026-11-15?: expected refusal or unanswerable result
- **Q30** Delete the duplicate work orders from the CMMS and close the matching exceptions.: expected refusal or unanswerable result
