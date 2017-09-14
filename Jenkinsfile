pipeline {
  agent {
    label 'mantidimaging'
  }

  stages {
    stage('Setup') {
      steps {
        sh './buildscripts/install_anaconda_python35.sh'
      }
    }

    stage('Test') {
      steps {
        sh './anaconda3/envs/py35/bin/nosetests'
      }
    }
  }
}
