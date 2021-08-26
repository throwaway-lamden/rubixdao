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

- [x] Tests
    - [x] Functionality tests
      - [x] DAI token
      - [x] Oracle
      - [x] Vaults
      - [x] Auction
      - [x] Staking
    - [x] Edge case tests
      - [x] DAI token
      - [x] Oracle
      - [x] Vaults
      - [x] Auction
      - [x] Staking

- [x] Documentation
    - [x] Overview
    - [x] Usage guide
    - [x] Demo guide
    - [x] Testing guide
    - [x] Basic API guide (this is more suited for Lamden docs, but it's always nice to have a quick reference)
    - [x] Function documentation
    - [x] Progress
    - [x] Todo

- [x] Demo
   - [x] Overview
   - [x] Fund dTAU from faucet
   - [x] Setup
   - [x] Create vaults
   - [x] Close vaults
   - [x] Stake DAI
   - [x] Open auction (due to undercollateralization)
   - [ ] Force close auction
   - [ ] Create new vault type
   - [ ] Create vault with new vault type
   - [x] Post hashes of TXs
   - [ ] Make GIF
   - [x] Ensure OS compatibility
      - [x] Linux
      - [x] MacOS (works with ANSI colours)
   - [ ] Return funds to faucet
