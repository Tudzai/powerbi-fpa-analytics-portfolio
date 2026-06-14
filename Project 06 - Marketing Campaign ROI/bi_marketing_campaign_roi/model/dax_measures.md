# DAX Measures

```DAX
Spend = SUM ( FactCampaignDaily[spend] )
Revenue = SUM ( FactCampaignDaily[revenue] )
Gross Profit = SUM ( FactCampaignDaily[gross_profit] )
Clicks = SUM ( FactCampaignDaily[clicks] )
Conversions = SUM ( FactCampaignDaily[conversions] )
New Customers = SUM ( FactCampaignDaily[new_customers] )

ROAS = DIVIDE ( [Revenue], [Spend] )
Marketing ROI = DIVIDE ( [Gross Profit] - [Spend], [Spend] )
CAC = DIVIDE ( [Spend], [New Customers] )
Conversion Rate = DIVIDE ( [Conversions], [Clicks] )

Target ROAS = AVERAGE ( DimChannel[target_roas] )
Target CAC = AVERAGE ( DimChannel[target_cac] )
ROAS vs Target = [ROAS] - [Target ROAS]
CAC vs Target = [Target CAC] - [CAC]
Spend Share = DIVIDE ( [Spend], CALCULATE ( [Spend], ALLSELECTED ( DimChannel[channel] ) ) )

Campaign Scale Score =
VAR campaignCount = COUNTROWS ( ALLSELECTED ( DimCampaign[campaign_name] ) )
VAR roasPct =
    DIVIDE ( RANKX ( ALLSELECTED ( DimCampaign[campaign_name] ), [ROAS], , ASC, DENSE ) - 1, campaignCount - 1 )
VAR roiPct =
    DIVIDE ( RANKX ( ALLSELECTED ( DimCampaign[campaign_name] ), [Marketing ROI], , ASC, DENSE ) - 1, campaignCount - 1 )
VAR inverseCacPct =
    1 - DIVIDE ( RANKX ( ALLSELECTED ( DimCampaign[campaign_name] ), [CAC], , ASC, DENSE ) - 1, campaignCount - 1 )
VAR profitPct =
    DIVIDE ( RANKX ( ALLSELECTED ( DimCampaign[campaign_name] ), [Gross Profit], , ASC, DENSE ) - 1, campaignCount - 1 )
RETURN
    IF ( campaignCount <= 1, BLANK (), ( roasPct * 0.4 + roiPct * 0.3 + inverseCacPct * 0.2 + profitPct * 0.1 ) * 100 )
```
