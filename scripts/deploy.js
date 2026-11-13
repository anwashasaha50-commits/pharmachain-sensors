
import { network } from "hardhat";

async function main() {
  const { ethers } = await network.create();

  const ColdChainAudit = await ethers.getContractFactory("ColdChainAudit");

  const audit = await ColdChainAudit.deploy();

  await audit.waitForDeployment();

  console.log(
    "ColdChainAudit contract deployed to:",
    await audit.getAddress()
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
