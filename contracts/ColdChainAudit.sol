// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ColdChainAudit {
    struct Reading {
        string batchId;
        uint256 temperature;
        uint256 humidity;
        bool isAnomaly;
        uint256 timestamp;
        address loggedBy;
    }

    mapping(string => Reading[]) public auditTrails;
    event ReadingLogged(string indexed batchId, uint256 temperature, bool isAnomaly, uint256 timestamp);

    function logReading(string memory _batchId, uint256 _temp, uint256 _humidity, bool _anomaly) public {
        Reading memory newReading = Reading({
            batchId: _batchId,
            temperature: _temp,
            humidity: _humidity,
            isAnomaly: _anomaly,
            timestamp: block.timestamp,
            loggedBy: msg.sender
        });
        
        auditTrails[_batchId].push(newReading);
        emit ReadingLogged(_batchId, _temp, _anomaly, block.timestamp);
    }

    function getAuditTrailCount(string memory _batchId) public view returns (uint256) {
        return auditTrails[_batchId].length;
    }
}
