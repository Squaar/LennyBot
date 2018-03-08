from setuptools import setup

setup(
    name='LennyBot',
    version='0.1',
    packages=['lennybot'],
    # package_dir={'': 'lennybot'},
    url='https://github.com/Squaar/LennyBot',
    license='MIT',
    author='Matt Dumford',
    author_email='mdumford99@gmail.com',
    description='A discord bot named Lenny',
    entry_points={
        'console_scripts': [
            'lennybot = lennybot.lennyrunner:main'
        ]
    }
)
