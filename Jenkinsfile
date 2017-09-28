pipeline {
  agent {
    label 'mantidimaging'
  }

  stages {
    stage('Setup') {
      steps {
        sh './buildscripts/install_anaconda_python35.sh'
          sh './buildscripts/install_anaconda_python27.sh'
      }
    }

    stage('Test') {
      steps {
        sh 'cd mantidimaging && git clean -Xf'
        sh './anaconda3/envs/py35/bin/nosetests'

        sh 'cd mantidimaging && git clean -Xf'
        sh './anaconda2/bin/nosetests'
      }
    }
  }
}
