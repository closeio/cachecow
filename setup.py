from setuptools import setup

setup(
    name='cachecow',
    version='0.1.2',
    url='http://github.com/closeio/cachecow',
    license='MIT',
    author='Stefan Wojcik',
    author_email='engineering@close.io',
    maintainer='Stefan Wojcik',
    maintainer_email='engineering@close.io',
    description='Fast and simple scaffolding for caching objects in Redis',
    test_suite='tests',
    tests_require=['mongoengine', 'redis'],
    packages=[
        'cachecow',
    ],
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    zip_safe=True
)
