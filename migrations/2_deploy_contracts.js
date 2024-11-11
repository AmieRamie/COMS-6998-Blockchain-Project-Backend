const ReceiptManager = artifacts.require("ReceiptManager");

module.exports = function (deployer) {
  const returnWindowDays = 30; // Set the desired return window (e.g., 30 days)
  deployer.deploy(ReceiptManager, returnWindowDays);
};
