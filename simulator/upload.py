import csv
import typer
import httpx
import asyncio

csv.field_size_limit(csv.field_size_limit() * 5)


def get_data(csvfilepath: str = "/tmp/all_the_news/all-the-news-2-1.csv"):
    ''' File column structure:
            0-7: (unused)
            8: content
            9-10: (unused)
            11: publication
    '''
    with open(csvfilepath) as f:
        for row in csv.reader(f):
            yield {'content': row[8], 'publication': row[11]}


async def upload_to_uri(uri: str, record_count):
    async with httpx.AsyncClient(verify=False, http2=True, headers={"access_token": "ijdf8h74nj"}) as c:
        row = get_data()
        next(row)  # Remove the header row
        for _ in range(record_count):
            await c.post(uri, json=next(row), timeout=3)

        print(f"submitted {record_count} records")


def runner(uri: str = 'http://0.0.0.0:8000/post/enqueue', record_count: int = 10):
    asyncio.run(upload_to_uri(uri, record_count))


def main():
    typer.run(runner)


if __name__ == "__main__":
    main()
