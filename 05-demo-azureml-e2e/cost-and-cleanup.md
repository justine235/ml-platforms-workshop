# Cost and cleanup

## Cost notes

- `Standard_DS3_v2` is the intended workshop compute size. The fact sheet verified a West Europe Linux retail-price anchor around **USD 0.272/hour** on 2026-10-18. Use that only as an order-of-magnitude planning number.
- **⚠ UNVERIFIED:** exact price in France Central or Sweden Central for the target subscription.
- **⚠ UNVERIFIED:** total workshop-day cost estimate of roughly USD 3-10. It depends on endpoint uptime, environment rebuilds, and any accidental scale-out.
- Online endpoints bill while deployments exist. Batch endpoints mainly bill when jobs run. ACR, storage, Log Analytics, and App Insights add small but non-zero overhead.

## Minimize cost

1. Keep the training cluster at `min nodes = 0` and `max nodes = 2`.
2. Prebuild the environment once, then reuse it.
3. Delete green after the demo if you no longer need the shadow deployment.
4. Keep the batch endpoint deployment at one instance for the workshop.
5. Shut down or delete any optional compute instance.

## Cleanup

```powershell
az ml online-endpoint delete --name fleet-risk-online --yes
az ml batch-endpoint delete --name fleet-risk-batch --yes
az group delete --name rg-fleet-aml-dev --yes --no-wait
```

## What to check before deleting

- Export any run artifacts or logs you want to keep.
- Confirm no other workshop session is using the shared resource group.
- If you deployed the optional AML registry, decide whether it should survive the demo day.
