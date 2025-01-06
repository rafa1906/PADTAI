import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="padtai",
    version="1.0.0",
    license='MIT License',                       
    description="PADTAI",
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=['padtai'],
    install_requires=[
        'clingo~=5.6.2',
        'bitarray~=2.9.2',
        'janus_swi~=1.5.1',
        'python-sat~=1.8.dev12',
        'popper_ilp @ https://github.com/logic-and-learning-lab/Popper/archive/1903c441082a344449988c6b52a46b7dde3fdc8a.zip'
    ],
    url="https://github.com/rafa1906/PADTAI",
    scripts=['./padtai.py', 'scripts/test_dataset.py'],
    packages=setuptools.find_packages(),
    python_requires='>=3.10'
)
