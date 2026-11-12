
import { network } from "hardhat";

async function main() {
  const { ethers } = await network.create();

  const SensorContract =
 	 await ethers.getContractFactory("SensorContract");

  const audit = await SensorContract.deploy();

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

