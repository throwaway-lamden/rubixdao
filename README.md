# lamden-mkr

## Progress:

- [x] Dai SC
  - [x] LST-001 
  - [x] Metadata
  - [x] Mint/burn
  - [x] Ownership change possible
  - [x] Total supply recorded

- [x] pETH equivalent
  - [x] Self equalizing after default # (This implementation uses increased redemption cost instead of decreased collateral)
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
    - [ ] Fee on default
    - [x] Oracle address
  - [x] Mutable state 
  - [x] Scalable
  - [x] Vaults can be added
  - [x] Vaults can be removed
  - [ ] Contract starts with default vault

- [x] Oracle
  - [x] Can display an arbitrary amount of token values
  - [x] Can be changed from main SC
  - [x] Has optimized stamp cost

- [ ] Tests
  - [ ] DAI token
  - [ ] Oracle
  - [ ] Vaults
  - [ ] Auction
  - [ ] Staking

- [ ] Documentation 
  - [ ] Overview
  - [ ] Usage guide
  - [ ] Testing guide
  - [ ] Basic API guide (this is more suited for Lamden docs, but it's always nice to have a quick reference)
  - [ ] Function documentation
  - [x] Todo

- [ ] Staking (DSR)
  - [x] Export excess tokens from Vaults (stability)
  - [ ] Stake to earn excess tokens
  - [ ] Allow multiple stakes/deposits

### TODO: 
Make tense consistent in progress

After documentation is completed, move `Progress` to progress.md
