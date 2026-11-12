// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SensorContract {
    uint256 public reading;

    function setReading(uint256 _reading) public {
        reading = _reading;
    }
}
