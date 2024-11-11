// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReceiptManager {
    address public seller;
    uint256 public returnWindow; // e.g., 30 days

    struct Receipt {
        uint256 purchaseAmount;
        uint256 purchaseTime;
        bool refundIssued;
        bool fundsReleased; // New flag to prevent duplicate fund release
    }

    // Mapping from buyer addresses to an array of their receipts
    mapping(address => Receipt[]) public receipts;

    event ReceiptIssued(address indexed buyer, uint256 purchaseAmount, uint256 purchaseTime, uint256 receiptIndex);
    event RefundIssued(address indexed buyer, uint256 refundAmount);
    event FundsReleased(address indexed seller, uint256 amount, uint256 receiptIndex);

    constructor(uint256 _returnWindow) {
        seller = msg.sender;
        returnWindow = _returnWindow * 1 days; // Convert return window to seconds
    }

    modifier onlySeller() {
        require(msg.sender == seller, "Only the seller can perform this action");
        _;
    }

    // Function to issue the receipt and hold funds in escrow for a specific buyer
    function issueReceipt(address _buyer) public payable onlySeller returns (uint256) {
        require(msg.value > 0, "No funds sent");

        // Create a new receipt and store it in the buyer's list
        receipts[_buyer].push(Receipt({
            purchaseAmount: msg.value,
            purchaseTime: block.timestamp,
            refundIssued: false,
            fundsReleased: false
        }));

        uint256 receiptIndex = receipts[_buyer].length - 1; // Index of the new receipt
        emit ReceiptIssued(_buyer, msg.value, block.timestamp, receiptIndex);
        
        // Return the index of the newly created receipt
        return receiptIndex;
    }

    // Buyer can request a return for a specific transaction within the return window
    function requestReturn(uint256 receiptIndex) public {
        require(receiptIndex < receipts[msg.sender].length, "Invalid receipt index");

        // Access the specific receipt of the buyer (msg.sender)
        Receipt storage receipt = receipts[msg.sender][receiptIndex];
        
        require(block.timestamp <= receipt.purchaseTime + returnWindow, "Return window has closed");
        require(!receipt.refundIssued, "Refund already issued");

        receipt.refundIssued = true;
        payable(msg.sender).transfer(receipt.purchaseAmount);

        emit RefundIssued(msg.sender, receipt.purchaseAmount);
    }

    // Function to release funds to the seller if the return window has expired
    function releaseFunds(address _buyer, uint256 receiptIndex) public onlySeller {
        require(receiptIndex < receipts[_buyer].length, "Invalid receipt index");

        Receipt storage receipt = receipts[_buyer][receiptIndex];
        require(!receipt.refundIssued, "Refund already issued");
        require(block.timestamp > receipt.purchaseTime + returnWindow, "Return window still open");
        require(!receipt.fundsReleased, "Funds already released"); // New check for funds release

        uint256 amountToRelease = receipt.purchaseAmount;
        receipt.fundsReleased = true; // Mark funds as released to prevent further releases

        payable(seller).transfer(amountToRelease);

        emit FundsReleased(seller, amountToRelease, receiptIndex);
    }

    // Function to retrieve receipt details
    function getReceipt(address _buyer, uint256 receiptIndex) public view returns (uint256, uint256, bool, bool) {
        require(receiptIndex < receipts[_buyer].length, "Invalid receipt index");

        Receipt memory receipt = receipts[_buyer][receiptIndex];
        return (receipt.purchaseAmount, receipt.purchaseTime, receipt.refundIssued, receipt.fundsReleased);
    }
}
