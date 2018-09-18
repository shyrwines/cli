from setuptools import setup

setup(
  name='shyr',
  entry_points={'console_scripts': ['shyr=shyr.shyr:main', 'image=shyr.image:main']},
  install_requires=['pillow', 'requests', 'squareconnect', 'xlrd'],
  dependency_links=['git+https://github.com/square/connect-python-sdk.git'],
  packages=['shyr']
)
