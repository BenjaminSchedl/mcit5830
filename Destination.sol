// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "./BridgeToken.sol";

contract Destination is AccessControl {
    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");
	mapping( address => address) public underlying_tokens;
	mapping( address => address) public wrapped_tokens;
	address[] public tokens;

	event Creation( address indexed underlying_token, address indexed wrapped_token );
	event Wrap( address indexed underlying_token, address indexed wrapped_token, address indexed to, uint256 amount );
	event Unwrap( address indexed underlying_token, address indexed wrapped_token, address frm, address indexed to, uint256 amount );

    constructor( address admin ) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(CREATOR_ROLE, admin);
        _grantRole(WARDEN_ROLE, admin);
    }

	function wrap(address _underlying_token, address _recipient, uint256 _amount ) public onlyRole(WARDEN_ROLE) {
        address wrappedTokenAddress = underlying_tokens[_underlying_token];
        require(wrappedTokenAddress != address(0), "Token not registered");

        BridgeToken wrappedToken = BridgeToken(wrappedTokenAddress);
        wrappedToken.mint(_recipient, _amount);

        emit Wrap(_underlying_token, wrappedTokenAddress, _recipient, _amount);

        console.log("Wrapped token address:", wrappedTokenAddress);
        console.log("Recipient:", _recipient);
        console.log("Amount:", _amount);
	}

	function unwrap(address _wrapped_token, address _recipient, uint256 _amount ) public {
        address underlyingTokenAddress = wrapped_tokens[_wrapped_token];
        require(underlyingTokenAddress != address(0), "Token not registered");

        BridgeToken wrappedToken = BridgeToken(_wrapped_token);
        wrappedToken.burnFrom(msg.sender, _amount);

        emit Unwrap(underlyingTokenAddress, _wrapped_token, msg.sender, _recipient, _amount);

        console.log("Unwrapped token address:", _wrapped_token);
        console.log("Recipient:", _recipient);
        console.log("Amount:", _amount);
	}

	function createToken(address _underlying_token, string memory name, string memory symbol ) public onlyRole(CREATOR_ROLE) returns(address) {
        require(underlying_tokens[_underlying_token] == address(0), "Token already created");

        BridgeToken newToken = new BridgeToken(_underlying_token, name, symbol, address(this));
        address newTokenAddress = address(newToken);

        underlying_tokens[_underlying_token] = newTokenAddress;
        wrapped_tokens[newTokenAddress] = _underlying_token;
        tokens.push(newTokenAddress);

        emit Creation(_underlying_token, newTokenAddress);

        console.log("Created token:", newTokenAddress);
        console.log("Underlying token mapped to:", underlying_tokens[_underlying_token]);
        console.log("Wrapped token mapped to:", wrapped_tokens[newTokenAddress]);

        return newTokenAddress;
	}

}


