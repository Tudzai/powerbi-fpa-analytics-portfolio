# Power Query M Source Snippets

Use these snippets if building the model manually from CSV.

```powerquery
let
    Source = Csv.Document(File.Contents("C:/Users/Win/OneDrive/Codex/Portfolio/BI/Project 18 - ESG Carbon Finance/data/prepared/fact_emissions.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
in
    PromotedHeaders
```

Repeat for each CSV in `data/prepared`.
