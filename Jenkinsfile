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

    stage('Clean Environment') {
      steps {
        sh 'cd mantidimaging && git clean -Xf'
      }
    }

    stage('Test') {
      steps {
        parallel python35: {
          sh './anaconda3/envs/py35/bin/nosetests'
        },
        python27: {
          sh './anaconda2/bin/nosetests'
        }
      }
    }
  }
}
