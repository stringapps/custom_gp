from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="custom_gp",
    version="0.0.1",
    description="Custom Gross Profit Report for ERPNext v15",
    author="String IT",
    author_email="admin@stringit.pro",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
