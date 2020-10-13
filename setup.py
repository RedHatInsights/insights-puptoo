from setuptools import find_packages, setup

setup(
    name="insights-puptoo",
    version="0.1",
    url="https://github.com/redhatinsights/insights-puptoo",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "prometheus-client==0.7.1",
        "logstash-formatter==0.5.17",
        "boto3==1.12.38",
        "watchtower==0.7.3",
        "requests==2.23.0",
        "insights-core==3.0.158",
        "confluent-kafka==1.5.0",
        "app-common-python==0.1.1"
    ],
    extras_require={"test": ["pytest>=5.4.1", "flake8>=3.7.9", "freezegun>=0.3.15"]},
    entry_points={"console_scripts": ["puptoo = puptoo.app:main"]},
)
