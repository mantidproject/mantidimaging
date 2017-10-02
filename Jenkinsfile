pipeline {
  agent {
    label 'mantidimaging'
  }

  stages {
    stage('Setup') {
      steps {
        sh '${WORKSPACE}/buildscripts/install_anaconda_python35.sh'
        sh '${WORKSPACE}/buildscripts/install_anaconda_python27.sh'
      }
    }

    stage('Test') {
      steps {
        sh 'cd mantidimaging && git clean -xdf'
        sh '${WORKSPACE}/anaconda3/envs/py35/bin/nosetests'

        sh 'cd mantidimaging && git clean -xdf'
        sh '${WORKSPACE}/anaconda2/bin/nosetests'

        sh 'cd mantidimaging && ${WORKSPACE}/anaconda3/envs/py35/bin/flake8'
      }
    }
  }
}
