pipeline {
  agent {
    label 'mantidimaging'
  }

  stages {
    stage('Setup - Miniconda') {
      steps {
        timeout(15) {
          sh '${WORKSPACE}/buildscripts/install_anaconda.sh -b'
        }
      }
    }

    stage('Setup - Python 2.7') {
      steps {
        timeout(30) {
          sh '${WORKSPACE}/buildscripts/create_conda_environment.sh ${WORKSPACE}/environment.yml mi27'
        }
      }
    }

    stage('Setup - Python 3.5') {
      steps {
        timeout(30) {
          sh '${WORKSPACE}/buildscripts/create_conda_environment.sh ${WORKSPACE}/environment-py35.yml mi35'
        }
      }
    }

    stage('Test - Python 2.7') {
      steps {
        timeout(2) {
          sh 'git clean -xdf --exclude="anaconda*"'
          sh '${WORKSPACE}/anaconda/envs/mi27/bin/nosetests --with-coverage --xunit-file=${WORKSPACE}/python27_nosetests.xml --xunit-testsuite-name=python27_nosetests || true'
          junit '**/python27_nosetests.xml'
        }
      }
    }

    stage('Test - Python 3.5') {
      steps {
        timeout(2) {
          sh 'git clean -xdf --exclude="anaconda*"'
          sh '${WORKSPACE}/anaconda/envs/mi35/bin/nosetests --with-coverage --xunit-file=${WORKSPACE}/python35_nosetests.xml --xunit-testsuite-name=python35_nosetests || true'
          junit '**/python35_nosetests.xml'
        }
      }
    }

    stage('Static Analysis - Flake8') {
      steps {
        timeout(5) {
          sh 'rm -f ${WORKSPACE}/flake8.log'
          sh 'cd mantidimaging && ${WORKSPACE}/anaconda/envs/mi27/bin/flake8 --exit-zero --output-file=${WORKSPACE}/flake8.log'
          step([$class: 'WarningsPublisher', parserConfigurations: [[parserName: 'Flake8', pattern: 'flake8.log']]])
        }
      }
    }

    stage('Documentation - HTML') {
      steps {
        timeout(1) {
          sh '${WORKSPACE}/anaconda/envs/mi27/bin/python setup.py docs_api'
          sh '${WORKSPACE}/anaconda/envs/mi27/bin/python setup.py docs -b html'
          warnings consoleParsers: [[parserName: 'Sphinx-build']]
        }
      }
    }

    stage('Documentation - QtHelp') {
      steps {
        timeout(1) {
          sh '${WORKSPACE}/anaconda/envs/mi27/bin/python setup.py docs -b qthelp'
        }
      }
    }
  }
}
