# Походження Golden dataset HW2

Власність визначена параметрами та observable; новий id сам по собі не зараховується. Kit-сценарії залишені added_in=l03.

| ID | Origin | Source | Oracle / assertion | Чому взято / новизна |
|---|---|---|---|---|
| FX-004 | kit | complaint | engine / tool_grounded_numeric | Retained kit scenario, not counted as own. |
| CMP-004 | kit | complaint | corpus / contains | Retained kit scenario, not counted as own. |
| FX-002 | kit | engine | engine / tool_grounded_numeric | Retained kit scenario, not counted as own. |
| FX-003 | kit | engine | engine / tool_grounded_numeric | Retained kit scenario, not counted as own. |
| FX-003-S | kit | engine | engine / contains | Retained kit scenario, not counted as own. |
| FX-005 | kit | engine | engine / tool_grounded_numeric | Retained kit scenario, not counted as own. |
| LIM-001 | kit | engine | engine / numeric | Retained kit scenario, not counted as own. |
| LIM-003 | kit | engine | engine / tool_result_numeric | Retained kit scenario, not counted as own. |
| DIS-001 | kit | engine | engine / contains | Retained kit scenario, not counted as own. |
| DIS-002-N | kit | engine | engine / not_regex | Retained kit scenario, not counted as own. |
| DIS-006 | kit | engine | engine / tool_result_flag | Retained kit scenario, not counted as own. |
| DIS-007 | kit | engine | engine / tool_result_flag | Retained kit scenario, not counted as own. |
| FX-006 | own | edge | engine / tool_grounded_numeric | New CUS-0007/1000EUR boundary, absent from kit generation plan. |
| FX-006-S | own | edge | engine / tool_result_numeric | New CUS-0007/1000EUR boundary, absent from kit generation plan. This case checks spread_pct rather than final_amount. |
| FX-007 | own | edge | engine / tool_grounded_numeric | New CUS-0007/1001EUR boundary, absent from kit generation plan. |
| FX-007-S | own | edge | engine / tool_result_numeric | New CUS-0007/1001EUR boundary, absent from kit generation plan. This case checks spread_pct rather than final_amount. |
| FX-008 | own | edge | engine / tool_grounded_numeric | New CUS-0001/380EUR boundary, absent from kit generation plan. |
| FX-008-S | own | edge | engine / tool_result_numeric | New CUS-0001/380EUR boundary, absent from kit generation plan. This case checks spread_pct rather than final_amount. |
| FX-009 | own | edge | engine / tool_grounded_numeric | New CUS-0001/381EUR boundary, absent from kit generation plan. |
| FX-009-S | own | edge | engine / tool_result_numeric | New CUS-0001/381EUR boundary, absent from kit generation plan. This case checks spread_pct rather than final_amount. |
| FX-010 | own | edge | engine / tool_grounded_numeric | New CUS-0002/200EUR boundary, absent from kit generation plan. |
| FX-011 | own | edge | engine / tool_grounded_numeric | New CUS-0002/201EUR boundary, absent from kit generation plan. |
| SWF-001 | own | complaint | engine / numeric | No SWIFT fee case exists in the kit set or unchanged engine generator. |
| SWF-002 | own | edge | engine / numeric | No SWIFT fee case exists in the kit set or unchanged engine generator. |
| CMP-C05 | own | edge | engine / tool_grounded_numeric | New 2000 EUR amount for CUS-0005; original C-05 is 6000 EUR and already represented by kit FX-003, so this is an edge variant, not a new reproduced complaint. |
| CMP-C11 | own | complaint | engine / tool_result_flag | PharmaPlus TX-0902 belongs to CUS-0009 in the complaint and is absent from the kit generator and demo. |
| CMP-C12 | own | complaint | engine / tool_result_flag | CloudServe TX-0201 is absent from both kit generator and demo eligibility cases. |
| CMP-C14 | own | complaint | engine / regex | New two-part completeness case: all reason codes plus the duplicate window; neither kit set nor generator has this combination. |
| LIM-HW2-DAILY | own | engine | engine / tool_result_numeric | CUS-0002 is absent from the kit limit generator plan (CUS-0010 and CUS-0001). |
| LIM-HW2-MONTHLY | own | engine | engine / tool_result_numeric | CUS-0002 is absent from the kit limit generator plan (CUS-0010 and CUS-0001). |
| TON-HW2-001 | own | complaint | human / judge | Authored situational rubric absent from kit. |
| TON-HW2-002 | own | edge | human / judge | Authored situational rubric absent from kit. |
| TON-HW2-003 | own | edge | human / judge | Authored situational rubric absent from kit. |
| TON-HW2-004 | own | edge | human / judge | Authored situational rubric absent from kit. |
| TON-HW2-005 | own | edge | human / judge | Authored situational rubric absent from kit. |
