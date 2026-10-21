# Data-agent config bundle

Paste the fields in this order when you build `da_fleet_recon` in the Fabric UI:

1. **Name / description**
   - Name: `da_fleet_recon`
   - Description: `Read-only Q&A over reconciled fleet telemetry, work orders, ERP assets, and frozen failure-risk scores.`
2. **Data source description**
   - Paste `data-source-description.md`
3. **Data source instructions**
   - Paste `data-source-instructions.md`
4. **Agent instructions**
   - Paste `agent-instructions.md`
5. **Schema notes**
   - Use `fabric-setup/schema-descriptions.md`
6. **Example queries**
   - Import `example-queries.json`

Recommended live demo order:

1. Add the lakehouse SQL analytics endpoint source.
2. Select only the gold/ml tables used in the examples.
3. Paste the three text fields above.
4. Import the example queries.
5. Test Q11, Q20, Q21, and Q30 before publishing.
