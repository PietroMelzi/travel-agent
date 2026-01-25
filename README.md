# Travel Agent

A travel assistant that helps with flights, hotels, cost of living, and more.

## Running locally

Activate the Poetry environment (`poetry shell` or `poetry run`), then run `python main.py`.

Add a `.env` file in the project root with:

```
OPENAI_API_KEY=<your-key>
SERP_API_KEY=<your-key>
RAPID_API_KEY=<your-key>
LITE_API_KEY=<your_key>
WANDB_API_KEY=<your-key>   # only if you want logging
```

`WANDB_API_KEY` is optional and only required if you want Weights & Biases logging.

## APIs

- **Flights:** [SerpAPI](https://serpapi.com/) — [Google Flights API](https://serpapi.com/google-flights-api) and [Autocomplete API](https://serpapi.com/google-flights-autocomplete-api).
- **Cost of living:** [RapidAPI](https://rapidapi.com/) — [Cost of Living and Prices](https://rapidapi.com/traveltables/api/cost-of-living-and-prices), updated to 2023.
- **Hotels:** [liteAPI](https://www.liteapi.travel/) - [Hotel Rates](https://docs.liteapi.travel/reference/post_hotels-rates)
