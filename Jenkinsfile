pipeline {
  agent {
    label 'mantidimaging'
  }

  stages {
    stage('Setup - Miniconda') {
      steps {
        timeout(15) {
          sh """
            export PATH=${WORKSPACE}/anaconda/bin:$PATH
            ${WORKSPACE}/buildscripts/install_anaconda.sh -b
            conda install -y conda-build
          """
        }
      }
    }

    stage('Setup - Python 3.5') {
      steps {
        timeout(30) {
          sh """
            export PATH=${WORKSPACE}/anaconda/bin:$PATH
            ${WORKSPACE}/buildscripts/create_conda_environment.sh ${WORKSPACE}/environment.yml mi35
          """
        }
      }
    }

    stage('Test - Python 3.5') {
      steps {
          timeout(2) {
          sh """
            export PATH=${WORKSPACE}/anaconda/envs/mi35/bin:$PATH
            git clean -xdf --exclude="anaconda*"
            nosetests --with-coverage --xunit-file=${WORKSPACE}/python35_nosetests.xml --xunit-testsuite-name=python35_nosetests || true
          """
          junit '**/python35_nosetests.xml'
        }
      }
    }

    stage('Static Analysis - Flake8') {
      steps {
        timeout(5) {
          sh """
            export PATH=${WORKSPACE}/anaconda/envs/mi35/bin:$PATH
            rm -f ${WORKSPACE}/flake8.log
            cd mantidimaging
            flake8 --exit-zero --output-file=${WORKSPACE}/flake8.log
          """
          step([$class: 'WarningsPublisher', parserConfigurations: [[parserName: 'Flake8', pattern: 'flake8.log']]])
        }
      }
    }

    stage('Documentation - HTML') {
      steps {
        timeout(1) {
          sh """
            export PATH=${WORKSPACE}/anaconda/envs/mi35/bin:$PATH
            python setup.py docs_api
            python setup.py docs -b html
          """
          warnings consoleParsers: [[parserName: 'Sphinx-build']]
        }
      }
    }

    stage('Documentation - QtHelp') {
      steps {
        timeout(1) {
          sh """
            export PATH=${WORKSPACE}/anaconda/envs/mi35/bin:$PATH
            python setup.py docs -b qthelp
          """
        }
      }
    }

    stage('Package - Conda') {
      steps {
        timeout(30) {
          sh """
            export PATH=${WORKSPACE}/anaconda/bin:$PATH
            cd buildscripts/conda
            ./build.sh
          """
        }
      }
    }
  }
}
