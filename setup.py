from setuptools import setup, find_packages

setup(
    name="insights-puptoo",
    version="0.1",
    url="https://github.com/redhatinsights/insights-puptoo",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "prometheus-client",
        "logstash-formatter",
        "boto3",
        "watchtower",
        "requests",
        "insights-core",
        "confluent-kafka",
    ],
    extras_require={
        "test": [
            "pytest",
            "flake8",
            "freezegun",
        ],
    },
    entry_points={
        "console_scripts": [
            "puptoo = puptoo.app:main",
        ],
    },
)
