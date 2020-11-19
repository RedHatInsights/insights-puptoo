/*
 * Requires: https://github.com/RedHatInsights/insights-pipeline-lib
 */

@Library("github.com/RedHatInsights/insights-pipeline-lib@v3") _

execSmokeTest (
    ocDeployerBuilderPath: "ingress/insights-puptoo",
    ocDeployerComponentPath: "ingress/insights-puptoo",
    ocDeployerServiceSets: "ingress,inventory,platform-mq",
    iqePlugins: ["iqe-e2e-plugin"],
    pytestMarker: "smoke"
)
