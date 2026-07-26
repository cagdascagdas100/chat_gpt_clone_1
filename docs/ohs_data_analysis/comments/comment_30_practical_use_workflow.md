# Comment 30 — Rebuild Section 5.3 around intended operational use

## Reviewer comment
`Burada yazılanlar da amacımızı yansıtmıyor. Bu bölümdeki amacımız, bu uygulamayı pratikte nasıl kullanacağız, buna cevap vermek. Kimler kullanacak, nasıl kullanacak, hangi modüller var vb. Benim automation’daki makalelerimi bir okuyarak kurgulanabilir burası da.`

## Selected heading
`5.3. The Practical Usage of the Model`

## Evidence reviewed
- Section 3.3 application architecture and workflow description.
- Section 4.5 application case example.
- Figures 15–18 and the visible application modules.
- The available analytical artifacts and preprocessing manifests.
- The current Section 5.3 text and all deployment/pilot claims appearing there.

## Editorial diagnosis
The current subsection does not answer the operational questions raised by the reviewer. Instead, it makes broad claims about transforming occupational safety practice, reducing workload, increasing awareness, creating peer accountability, enabling community-based reporting, and operating a pilot in specified numbers of companies and employees. The available revision package does not contain an auditable deployment protocol, recruitment record, ethics documentation, usage logs, survey results, field-effectiveness results, or evidence supporting the stated pilot sample and expansion plan.

The section must therefore describe the **intended use pathway** of the verified application rather than presenting unverified implementation effects.

## Revised section title
`5.3. Intended Operational Use of the OSH-RA Mobile Decision-Support Application`

The word `model` should not be used for the complete software system, consistent with Comment 27.

## Intended users
1. **Primary user:** a construction worker or equipment user completing a pre-task or condition-based assessment for the work area and machinery being used.
2. **Reviewing users:** occupational-safety professionals, competent persons, and site supervisors who verify the reported conditions, review the risk outputs, and decide which controls require immediate implementation.
3. **Management use:** project or company management may use the control and cost modules to plan resources, but cost estimates must not be used to postpone mandatory safety controls or replace legal duties.

No employer dashboard, organization-wide aggregation function, or role-specific access-control workflow is demonstrated in the supplied screenshots; these functions must not be claimed as implemented unless software evidence is provided.

## Operational workflow
1. The user enters the personal and contextual variables requested by the application, such as age group, education level, accident history, company accident history, wage band, shift, and season.
2. The user follows the hierarchical work-selection path: sector, category, subcategory, work section, operated machine, and machine-condition questions.
3. Multiple machines and observed faults may be recorded in one assessment where the interface supports them.
4. The application applies stored outputs from offline-trained classifiers and deterministic aggregation/ranking rules to the entered data.
5. The results screen presents the risk summary, body-region distribution, and prioritized machine–fault scenarios. Any overall composite percentage remains subject to the unresolved normalization and weighting decisions in Comments 17 and 20.
6. The user opens the detailed modules to review controls, potential consequences, legal information, and the scenario-based cost calculation.
7. The assessment should be repeated when the worker profile, shift, work area, selected equipment, or observed equipment condition changes. The current system must not be described as continuous real-time monitoring.

## Verified application modules
- **Visual Results:** displays the risk distribution by body region and related detailed values.
- **Precautions:** presents equipment- and fault-specific control measures.
- **What If No Precautions?:** presents modeled consequence descriptions for unresolved faults.
- **My Legal Rights:** presents general legal-information content associated with the selected condition; it is not individualized legal advice.
- **Cost Analysis:** presents preventive-cost inputs and scenario-based payment/risk-cost fields. The terminology and units remain governed by Comments 8, 9, 20, and 21.

## Practical decision points
The application may support the following decisions, subject to confirmation by a competent person:
- whether a machine or component requires inspection, maintenance, repair, isolation, or removal from service before work begins;
- which reported faults and scenarios require priority attention;
- which preventive measures should be communicated and verified during pre-task planning;
- which body regions and injury consequences should be emphasized in task-specific safety communication;
- which cost items must be budgeted to implement required controls.

The application is a decision-support aid. It does not replace statutory risk assessment, engineering inspection, competent-person judgment, emergency procedures, or regulatory compliance.

## Deployment and ethical safeguards
- Personal and workplace data should be minimized, access-controlled, and retained only for a defined operational purpose.
- Personal-risk outputs must not be used to blame workers, discriminate in job allocation, or deny employment or work opportunities.
- Cost outputs must not be interpreted as permission to trade required safety controls against financial savings.
- The present study does not establish usability, user acceptance, behavioral change, accident reduction, economic benefit, field effectiveness, or external validity.
- Claims that the application is already piloted in `10 companies and approximately 250 employees`, or that a `50-company / 2,500–3,000-employee` pilot is planned, will be removed unless protocol dates, recruitment records, ethics/privacy procedures, usage logs, analysis plans, and results are supplied.

## Preferred replacement text for Section 5.3
`The OSH-RA mobile decision-support application is intended to support pre-task and condition-based safety assessment in construction work. The primary interaction is worker-facing: the user enters the requested personal and work-context variables, selects the relevant work area and operated machines, and records observable machine faults through the application’s structured questions. Occupational-safety professionals, competent persons, and site supervisors may then review the reported conditions and outputs when determining whether inspection, maintenance, repair, isolation, or other preventive controls are required before work proceeds.`

`After the inputs are completed, the application applies the stored outputs of offline-trained classifiers and deterministic risk-aggregation and ranking rules. The results interface presents a risk summary, body-region-specific values, and prioritized machine–fault scenarios. The detailed modules provide equipment-specific precautions, modeled consequences if controls are not implemented, general legal information, and a scenario-based cost analysis. Assessments should be repeated whenever the worker profile, shift, work area, selected equipment, or observed equipment condition changes; the application does not perform continuous real-time site monitoring.`

`The application is designed as a supplementary decision-support tool rather than a replacement for statutory risk assessment, competent-person inspection, engineering judgment, or regulatory duties. The present evaluation is limited to internal analytical validation and an illustrative application case. It does not establish application-level usability, field effectiveness, accident reduction, or economic benefit. These outcomes require a prospectively defined field study with documented users, deployment settings, privacy safeguards, usage logs, and prespecified evaluation measures.`

## Manuscript-wide consistency actions
- Replace `The Practical Usage of the Model` with the revised title above.
- Remove unsupported claims of reduced OSH workload, increased awareness, peer accountability, community-of-practice reporting, and sustained safety-culture effects unless evaluated data are supplied.
- Remove the pilot-company and employee counts unless auditable study documentation is supplied.
- Keep module names and descriptions consistent with Figures 16–18 and Comments 22–23.
- Keep `overall risk` wording conditional on Comments 17 and 20.
- Keep payment-day, indemnity, and cost terminology conditional on Comments 8, 9, and 21.
- Do not describe the workflow as real-time, continuously updating, or multimodal.

## Reviewer-response draft
`Revised. Section 5.3 was rewritten to explain the intended operational use of the OSH-RA application: the intended users, the stepwise input workflow, the verified application modules, the resulting decision points, and the limits of the tool. Unsupported statements concerning workload reduction, safety-culture effects, community reporting, pilot deployment, and application effectiveness were removed. The revised text explicitly describes OSH-RA as a supplementary decision-support application and not as a replacement for statutory risk assessment or competent-person judgment.`

## Status
Finalized. The subsection can be revised without additional evidence by removing the unsupported deployment and effectiveness claims. Any future restoration of pilot claims requires auditable study documentation.