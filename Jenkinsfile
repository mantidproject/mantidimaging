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
            ${WORKSPACE}/source/buildscripts/install_anaconda.sh -b
            conda install -y conda-build
            conda install -y anaconda-client
          """
        }
      }
    }

    stage('Setup - Python 3.5') {
      steps {
        timeout(30) {
          sh """
            export PATH=${WORKSPACE}/anaconda/bin:$PATH
            ${WORKSPACE}/source/buildscripts/create_conda_environment.sh ${WORKSPACE}/source/environment.yml mi35
          """
        }
      }
    }

    stage('Test - Python 3.5') {
      steps {
          timeout(2) {
          sh """
            export PATH=${WORKSPACE}/anaconda/envs/mi35/bin:$PATH
            cd ${WORKSPACE}/source
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
            cd ${WORKSPACE}/source/mantidimaging
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
            cd ${WORKSPACE}/source
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
            cd ${WORKSPACE}/source
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
            rm -rf ${WORKSPACE}/mantidimaging_conda
            conda-build --croot ${WORKSPACE}/mantidimaging_conda ${WORKSPACE}/source/conda/mantidimaging
            tar -cvzf ${WORKSPACE}/mantidimaging_conda.tar.gz ${WORKSPACE}/mantidimaging_conda/
          """
          archiveArtifacts 'mantidimaging_conda.tar.gz'
        }
      }
    }

    stage('Package - Publish') {
      when {
        expression {
          return env.GIT_BRANCH == 'origin/master';
        }
      }
      steps {
        withCredentials([string(credentialsId: 'anaconda-cloud-token', variable: 'ANACONDA_CLOUD_TOKEN')]) {
          sh """
            export PATH=${WORKSPACE}/anaconda/bin:$PATH
            anaconda -t $ANACONDA_CLOUD_TOKEN upload --force -u mantid -l nightly `ls mantidimaging_conda/linux-64/mantidimaging-*.tar.bz2`
          """
        }
      }
    }
  }
}
