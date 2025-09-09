#!/bin/groovy
@Library('deployer') _

properties([
    parameters([
        gitParameter(name: 'BRANCH_NAME',
                     type: 'PT_BRANCH',
                     defaultValue: 'origin/',
                     branchFilter: '.*',
                     quickFilterEnabled: true,
                     sortMode: 'ASCENDING',
                     selectedValue: 'DEFAULT',
                     description: 'Select the Git branch to build')
    ])
])

pipeline {
    agent {
        kubernetes {
            cloud 'prod-eks-cluster'
            inheritFrom "prod-eks-jenkins-docker-builder"
        }
    }
    environment {
        MAIN_BRANCH = "origin/"
    }
    options {
        timestamps()
        timeout(time: 30, unit: "MINUTES")
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '5'))
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }
    stages {
        stage('Job Setup and Validation') {
            steps {
                script {
                    env.CURRENT_STAGE = env.STAGE_NAME
                    deployerJobValidation.validate()
                    deployerInspect.instance()
                    deployerPipelineConfig.getConfig()
                }
            }
        }
        stage('Provision QA Infrastructure') {
            steps {
                script {
                    env.CURRENT_STAGE = env.STAGE_NAME
                    deployerDeploy.prepareInfra("qa")
                }
            }
        }
        stage('Build and Push Docker Image') {
            steps {
                script {
                    env.CURRENT_STAGE = env.STAGE_NAME
                    deployerDocker.buildPushDockerImage()
                }
            }
        }
        stage('Deploy to QA') {
            steps {
                script {
                    env.CURRENT_STAGE = env.STAGE_NAME
                    deployerDeploy.deploy("qa")
                }
            }
        }
        stage('Quality Analysis') {
            parallel {
                stage('Integration Test') {
                    steps {
                        echo 'Run integration tests here...'
                    }
                }
                stage('Smoke tests') {
                    when {
                        expression {
                            env.EXECUTE_SMOKE_TESTS == "true"
                        }
                    }
                    steps {
                        echo 'Running smoke tests'
                        script {
                            env.CURRENT_STAGE = env.STAGE_NAME
                            def responseCode = sh(
                                script: "curl -o /dev/null -s -w '%{http_code}' -X HEAD -I https://${SERVICE_NAME}.qa.givelify.com/health-check",
                                returnStdout: true
                            ).trim()
                            if (responseCode != '200') {
                                error "Smoke test failed! Received HTTP response code: ${responseCode}"
                            } else {
                                echo "Smoke test passed! Received HTTP response code: ${responseCode}"
                            }
                        }
                    }
                }
            }
        }
        stage('Approval for PROD Deployment') {
            when {
                env.BRANCH_NAME == env.MAIN_BRANCH
            }
            steps {
                script {
                    env.CURRENT_STAGE = env.STAGE_NAME
                    deployerDeploy.approve(15) // 15 minutes to approve
                }
            }
        }
        stage('Provision PROD Infrastructure') {
            when {
                env.BRANCH_NAME == env.MAIN_BRANCH
            }
            steps {
                script {
                    env.CURRENT_STAGE = env.STAGE_NAME
                    deployerDeploy.prepareInfra("prod")
                }
            }
        }
        stage('Deploy to PROD') {
            when {
                env.BRANCH_NAME == env.MAIN_BRANCH
            }
            steps {
                script {
                    env.CURRENT_STAGE = env.STAGE_NAME
                    deployerDeploy.deploy("prod")
                }
            }
        }
    }
    post {
        always {
            script {
                deployerInspect.environment()
                deployerDocker.pruneDocker()
                cleanWs()
            }
        }
        unsuccessful {
            script {
                deployerNotify.slackNotification(env.CURRENT_STAGE)
            }
        }
    }
}