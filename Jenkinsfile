pipeline {
  agent {
    label 'mantidimaging'
  }

  stages {
    stage('Setup') {
      steps {
        timeout(15) {
          sh '${WORKSPACE}/buildscripts/install_anaconda_python35.sh -b'
          sh '${WORKSPACE}/anaconda3/envs/py35/bin/pip install -r test-requirements.txt'
          sh '${WORKSPACE}/buildscripts/install_anaconda_python27.sh -b'
          sh '${WORKSPACE}/anaconda2/bin/pip install -r test-requirements.txt'
          sh '${WORKSPACE}/anaconda2/bin/pip install -r setup-requirements.txt'
        }
      }
    }

    stage('Test - Python 3.5') {
      steps {
        timeout(2) {
          sh 'git clean -xdf --exclude="anaconda*"'
          sh '${WORKSPACE}/anaconda3/envs/py35/bin/nosetests --xunit-file=${WORKSPACE}/python35_nosetests.xml --xunit-testsuite-name=python35_nosetests || true'
          junit '**/python35_nosetests.xml'
        }
      }
    }

    stage('Test - Python 2.7') {
      steps {
        timeout(2) {
          sh 'git clean -xdf --exclude="anaconda*"'
          sh '${WORKSPACE}/anaconda2/bin/nosetests --xunit-file=${WORKSPACE}/python27_nosetests.xml --xunit-testsuite-name=python27_nosetests || true'
          junit '**/python27_nosetests.xml'
        }
      }
    }

    stage('Flake8') {
      steps {
        timeout(5) {
          sh 'rm -f ${WORKSPACE}/flake8.log'
          sh 'cd mantidimaging && ${WORKSPACE}/anaconda3/envs/py35/bin/flake8 --exit-zero --output-file=${WORKSPACE}/flake8.log'
          step([$class: 'WarningsPublisher', parserConfigurations: [[parserName: 'Flake8', pattern: 'flake8.log']]])
        }
      }
    }

    stage('Build Documentation') {
      steps {
        timeout(5) {
          sh '${WORKSPACE}/anaconda2/bin/python setup.py docs -b html'
          sh '${WORKSPACE}/anaconda2/bin/python setup.py docs -b qthelp'
        }
      }
    }
  }
}
