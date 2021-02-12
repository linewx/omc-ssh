from setuptools import setup, find_packages
install_requires = [
    'omc>=0.2.1'
]


setup(
    name='omc-ssh',
    version="0.0.3",
    description='ssh plugin for omc',
    license='MIT',
    author='Lu Ganlin',
    author_email='linewx1981@gmail.com',
    url='https://github.com/linewx/omc-ssh',
    packages=find_packages(),
    # package_data={'omc.config': ['*.yaml'], 'omc.lib': ['**', '**/*', '**/**/*']},
    install_requires=install_requires,
)
