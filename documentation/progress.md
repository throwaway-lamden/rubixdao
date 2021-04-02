### Progress:

- [x] Dai SC
   - [x] LST-001
    - [x] Metadata
    - [x] Mint/burn
    - [x] Ownership change possible
    - [x] Total supply recorded

- [x] pETH equivalent (This implementation uses increased redemption cost instead of decreased collateral)
   - [x] Self equalizing after default
    - [x] Uses stability pool after default
    - [x] Additional manual burn possible
       - [x] Allow manual burns from anyone

- [x] Auction SC (can be simplified)
   - [x] Instant buy for small profit
    - [x] Standard auction

- [x] Vaults
   - [x] Has settable values
       - [x] Collateral type
        - [x] Minimum collateralization
        - [x] Stability cost
        - [x] Fee on default
        - [x] Oracle address
    - [x] Mutable state
    - [x] Scalable
    - [x] Vaults can be added
    - [x] Vaults can be removed
    - [x] Contract starts with default vault

- [x] Oracle
   - [x] Can display an arbitrary amount of token values
    - [x] Can be changed from main SC
    - [x] Has optimized stamp cost

- [x] Staking (DSR)
   - [x] Export excess tokens from Vaults (stability)
    - [x] Can mint tokens if stability pool is not sufficent
    - [x] Updates pETH ratio
    - [x] Has settable burden for every liquidity pool
    - [x] Stake to earn excess tokens
    - [x] Allow multiple stakes/deposits

- [ ] Tests
    - [ ] Functionality tests
      - [x] DAI token
      - [x] Oracle
      - [ ] Vaults
      - [ ] Auction
      - [ ] Staking
    - [ ] Edge case tests
      - [x] DAI token
      - [x] Oracle
      - [ ] Vaults
      - [ ] Auction
      - [ ] Staking

- [ ] Documentation
    - [ ] Overview
    - [ ] Usage guide
    - [ ] Testing guide
    - [ ] Basic API guide (this is more suited for Lamden docs, but it's always nice to have a quick reference)
    - [ ] Function documentation
    - [x] Progress
    - [x] Todo
