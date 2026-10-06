// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EvidenceStorage {
    struct Evidence {
        string evidenceHash;
        string caseID;
        uint256 timestamp;
    }

    Evidence[] public records;

    function storeEvidence(string memory _hash, string memory _caseID) public {
        records.push(Evidence(_hash, _caseID, block.timestamp));
    }

    function getEvidence(uint index) public view returns (string memory, string memory, uint256) {
        Evidence memory e = records[index];
        return (e.evidenceHash, e.caseID, e.timestamp);
    }

    function getCount() public view returns (uint) {
        return records.length;
    }
}