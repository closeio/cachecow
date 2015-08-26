from setuptools import setup

setup(
    name='cachecow',
    version='0.1.1',
    url='http://github.com/closeio/cachecow',
    license='BSD',
    author='Stefan Wojcik',
    author_email='wojcikstefan@gmail.com',
    maintainer='Stefan Wojcik',
    maintainer_email='wojcikstefan@gmail.com',
    description='Simple module for caching objects in Redis',
    long_description=__doc__,
    packages=[
        'cachecow',
    ],
    test_suite='tests',
    zip_safe=True,
    platforms='any',
    setup_requires=[
        'redis',
        'xxhash',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
