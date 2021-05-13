from setuptools import setup, find_packages

setup(
    name="ingestion",
    version="0.0.1",
    author="Ben Lambert",
    author_email="support@cloudacademy.com",
    description="A demo application created to accompany a Python course.",
    keywords="learn python cloud academy",
    url="http://cloudacademy.com",
    packages=find_packages(),
    entry_points={"console_scripts": [
        "ingestiond=ingest.backend:main",
        "getdataset=simulator.download:download_and_extract",
        "uploaddataset=simulator.upload:main",
    ]},
    install_requires=[
        "fastapi==0.58.0",
        "google-cloud-firestore==1.7.0",
        "pydantic==1.6.2",
        "uvicorn==0.11.7",
        "gunicorn==20.0.4",
        "passlib==1.7.2",
        "bcrypt==3.1.7",
        "PyJWT==1.7.1",
        "spacy==2.3.2",
        "spacy-lookups-data==0.3.2",
        "typer==0.3.0",
        "httpx==0.13.3",
        "supervisor==4.2.0",
    ],
    extras_require={
        "dev": [
            "pytest==5.4.3",
        ],
        "web": [
            "wordcloud==1.7.0",
            "falcon",
            "falcon==2.0.0",
            "google-cloud-storage==1.29.0",
        ]
    }

)
