# Data Dictionary

| Table | Grain | Key | Columns |
|---|---|---|---|
| dim_date | One calendar day | DateKey | DateKey, Date, MonthStart, Year, Quarter, MonthNumber, MonthName, MonthYear, MonthIndex, IsLatestCompleteMonth |
| dim_country | One country | CountryCode | CountryCode, Country, Region, CountryRiskScore, CountryRiskTier |
| dim_corridor | One origin-destination corridor | CorridorKey | CorridorKey, OriginCountryCode, DestinationCountryCode, Corridor, CorridorName, CorridorRiskScore, CorridorRiskTier |
| dim_channel | One transaction channel | ChannelKey | ChannelKey, Channel, ChannelMode, ChannelRiskScore |
| dim_product | One banking/payment product | ProductKey | ProductKey, Product, ProductFamily, ProductRiskScore |
| dim_rule | One detection rule | RuleKey | RuleKey, RuleName, Typology, RuleSeverity, RuleStatus, RuleOwner, RuleRiskScore, LastTunedDate |
| dim_analyst | One analyst | AnalystKey | AnalystKey, Analyst, AnalystTier, Queue |
| dim_customer | One customer profile | CustomerKey | CustomerKey, Customer, CustomerSegment, CustomerType, HomeCountryCode, HomeCountry, CustomerRiskScore, CustomerRiskTier, PEPFlag, WatchlistFlag, KYCStatus, OnboardingDate |
| fact_transactions | One financial transaction | TransactionKey | TransactionKey, DateKey, CustomerKey, CorridorKey, ChannelKey, ProductKey, AmountUSD, RiskScore, IsFlagged, PrimaryRuleKey, RoundDollarFlag, TransactionType |
| fact_alerts | One alert generated from a flagged transaction | AlertKey | AlertKey, TransactionKey, DateKey, AlertDateKey, CustomerKey, RuleKey, CorridorKey, ChannelKey, ProductKey, AlertAmountUSD, RiskScore, Severity, AlertStatus, IsFalsePositive, IsTruePositive, EscalatedToCase, CaseKey, ClosedDateKey, HoursToDisposition |
| fact_cases | One investigation case opened from an escalated alert | CaseKey | CaseKey, AlertKey, CreatedDateKey, ClosedDateKey, CustomerKey, RuleKey, CorridorKey, AnalystKey, CasePriority, CaseStatus, Outcome, SARFiled, SLAHours, AgeDays, HoursToClose, IsOverdue, CaseAmountUSD |
| fact_rule_governance | One rule governance event | GovernanceKey | GovernanceKey, RuleKey, ChangeDateKey, ChangeType, ChangeReason, ApprovalStatus, ApprovedBy, PrecisionBefore, PrecisionAfter, AlertVolumeDeltaPct |
