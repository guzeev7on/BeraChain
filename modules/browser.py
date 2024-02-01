from pyuseragents import random as random_ua
from time import sleep, time
from uuid import uuid4
from json import loads
import tls_client
import requests
import random

from modules.utils import logger, sleeping
import settings


class Browser:
    def __init__(self):
        self.max_retries = 5
        self.session = tls_client.Session(
            client_identifier=random.choice([
                'Chrome110',
                'chrome111',
                'chrome112'
            ]),
            random_tls_extension_order=True
        )
        self.session.timeout_seconds = 60
        self.session.headers['User-Agent'] = random_ua()

        if settings.PROXY not in ['http://log:pass@ip:port', '']:
            self.change_ip()
            self.session.proxies.update({'http': settings.PROXY, 'https': settings.PROXY})
        else:
            logger.warning('You are not using proxy')


    def change_ip(self):
        if settings.CHANGE_IP_LINK not in ['https://changeip.mobileproxy.space/?proxy_key=...&format=json', '']:
            while True:
                r = self.session.get(settings.CHANGE_IP_LINK)
                if r.status_code == 200:
                    logger.info(f'[+] Proxy | Changed ip: {r.text}')
                    return True
                logger.warning(f'[•] Proxy | Change IP error: {r.text} | {r.status_code}')
                sleep(10)


    def login_in_galxe(self, address, text, signature):
        retry = 0
        self.address = address.lower()
        while True:
            try:
                payload = {
                    "operationName": "SignIn",
                    "variables": {
                        "input": {
                            "address": self.address,
                            "addressType": "EVM",
                            "message": text,
                            "signature": signature,
                        }
                    },
                    "query": "mutation SignIn($input: Auth) {\n  signin(input: $input)\n}\n"
                }
                response = self.session.post('https://graphigo.prd.galaxy.eco/query', json=payload)

                if response.status_code == 200:
                    self.session.headers['authorization'] = response.json()['data']['signin']
                    logger.info(f"[+] Galxe | Successfully logged in Galxe")
                    return True
                else:
                    retry += 1
                    if retry >= self.max_retries:
                        raise ValueError(f'Galxe | Get Bearer token error: {response.status_code}\n{response.text}')
                    logger.warning(f'[·] Galxe | Cant get Bearer token, trying again...')
                    sleep(10)
            except Exception as err:
                retry += 1
                if retry >= self.max_retries:
                    raise ValueError(f'Galxe | Get Bearer token error: {response.status_code}\n{response.text}')
                try: error_text = f'| {response.status_code}\n{response.text}'
                except: error_text = ''
                logger.error(f'[·] Galxe | Get Bearer error: {err} {error_text}')
                sleep(15)


    def get_galaxy_acc_info(self):
        retry = 0
        while True:
            try:
                url = 'https://graphigo.prd.galaxy.eco/query'
                payload = {
                    "operationName": "BasicUserInfo",
                    "variables": {
                        "address": self.address
                    },
                    "query": "query BasicUserInfo($address: String!) {\n  addressInfo(address: $address) {\n    id\n    username\n    avatar\n    address\n    evmAddressSecondary {\n      address\n      __typename\n    }\n    hasEmail\n    solanaAddress\n    aptosAddress\n    seiAddress\n    injectiveAddress\n    flowAddress\n    starknetAddress\n    bitcoinAddress\n    hasEvmAddress\n    hasSolanaAddress\n    hasAptosAddress\n    hasInjectiveAddress\n    hasFlowAddress\n    hasStarknetAddress\n    hasBitcoinAddress\n    hasTwitter\n    hasGithub\n    hasDiscord\n    hasTelegram\n    displayEmail\n    displayTwitter\n    displayGithub\n    displayDiscord\n    displayTelegram\n    displayNamePref\n    email\n    twitterUserID\n    twitterUserName\n    githubUserID\n    githubUserName\n    discordUserID\n    discordUserName\n    telegramUserID\n    telegramUserName\n    enableEmailSubs\n    subscriptions\n    isWhitelisted\n    isInvited\n    isAdmin\n    accessToken\n    __typename\n  }\n}\n"
                }

                response = self.session.post(url, json=payload)
                if response.status_code == 200:
                    try:
                        self.acc_info = response.json()['data']['addressInfo']

                        if self.acc_info['id'] == "":
                            self.create_new_acc()
                            return self.get_galaxy_acc_info()
                        else:
                            return self.acc_info
                    except:
                        raise ValueError(f'Galxe | Not found addressInfo.id: {response.text}')
                else:
                    raise ValueError(f'Galxe | Get Basic Info bad response: {response.status_code} {response.text}')

            except Exception as err:
                retry += 1
                if retry >= self.max_retries:
                    try: error_text = f'\n{response.status_code} {response.text}'
                    except: error_text = ''
                    raise ValueError(f'Galxe | Get Basic Info error: {err}{error_text}')
                logger.error(f'[·] Galxe | Cant get galaxy acc info | {err}')
                sleep(15)


    def get_available_nickname(self):
        while True:
            r = self.session.get('https://story-shack-cdn-v2.glitch.me/generators/username-generator')
            nickname = r.json()['data']['name']
            if random.random() < 0.33: nickname = nickname.upper()
            if random.random() < 0.33: nickname = nickname.lower()
            if random.random() < 0.33: nickname = nickname[:random.randint(2, 6)] + '_' + nickname[-random.randint(2, 6):]
            if random.random() < 0.33:
                if random.random() < 0.5: nickname = '_' + nickname
                nickname = str(random.randint(0, 1000)) + nickname
            if random.random() < 0.33:
                if random.random() < 0.5: nickname += '_'
                nickname += str(random.randint(0, 1000))

            url = 'https://graphigo.prd.galaxy.eco/query'
            payload = {
                "operationName": "IsUsernameExisting",
                "variables": {
                    "username": nickname
                },
                "query": "query IsUsernameExisting($username: String!) {\n  usernameExist(username: $username)\n}\n"
            }

            response = self.session.post(url, json=payload)
            if response.status_code == 200:
                if response.json()['data']['usernameExist'] == False:
                    return nickname
            else:
                logger.warning(f'[·] Galxe | Сant get available nickname, trying again...')


    def create_new_acc(self):
        while True:

            nickname = self.get_available_nickname()

            url = 'https://graphigo.prd.galaxy.eco/query'
            payload = {
                "operationName": "CreateNewAccount",
                "variables": {
                    "input": {
                        "schema": f"EVM:{self.address}",
                        "socialUsername": "",
                        "username": nickname
                    }
                },
                "query": "mutation CreateNewAccount($input: CreateNewAccount!) {\n  createNewAccount(input: $input)\n}\n"
            }

            response = self.session.post(url, json=payload)
            if response.status_code == 200:
                logger.info(f'[+] Galxe | Created profile with nickname {nickname}')
                return True
            else:
                logger.warning(f'[·] Galxe | Cant update nickname, trying again...')


    def reload_task(self, cred_id: str):
        payload = {
            "operationName": "SyncCredentialValue",
            "variables": {
                "input": {
                    "syncOptions": {
                        "credId": cred_id,
                        "address": self.address,
                    }
                }
            },
            "query": "mutation SyncCredentialValue($input: SyncCredentialValueInput!) {\n  syncCredentialValue(input: $input) {\n    value {\n      address\n      spaceUsers {\n        follow\n        points\n        participations\n        __typename\n      }\n      campaignReferral {\n        count\n        __typename\n      }\n      gitcoinPassport {\n        score\n        lastScoreTimestamp\n        __typename\n      }\n      walletBalance {\n        balance\n        __typename\n      }\n      multiDimension {\n        value\n        __typename\n      }\n      allow\n      survey {\n        answers\n        __typename\n      }\n      quiz {\n        allow\n        correct\n        __typename\n      }\n      __typename\n    }\n    message\n    __typename\n  }\n}\n"
        }
        if cred_id == '287387120990593025':
            payload['variables']['input']['syncOptions']['gitcoin'] = {'captcha': self.solve_geecaptcha()}

        r = self.session.post('https://graphigo.prd.galaxy.eco/query', json=payload)

        if 'failed to verify recaptcha token' in r.text:
            logger.warning(f'[-] Galxe | Outdated `w` token! Dont stop this soft, just change it in `w.txt`')
            sleep(10)
            return self.reload_task(cred_id=cred_id)
        elif cred_id == '287387120990593025':
            return r.json()['data']['syncCredentialValue']['value']['gitcoinPassport']['score'] >= 20
        elif r.json()['data']['syncCredentialValue']['value']['allow'] == True:
            logger.info(f'[+] Galxe | Task №{cred_id} verified')
            return True
        else:
            logger.warning(f"Cred {cred_id} not verified: {r.json()['data']['syncCredentialValue']['message']}")


    def claim(self, retry=0):
        payload = {
            "operationName": "PrepareParticipate",
            "variables": {
                "input": {
                    "signature": "",
                    "campaignID": "GCTN3ttM4T",
                    "address": self.address,
                    "mintCount": 1,
                    "chain": "ETHEREUM",
                    "captcha": self.solve_geecaptcha()
                }
            },
            "query": "mutation PrepareParticipate($input: PrepareParticipateInput!) {\n  prepareParticipate(input: $input) {\n    allow\n    disallowReason\n    signature\n    nonce\n    mintFuncInfo {\n      funcName\n      nftCoreAddress\n      verifyIDs\n      powahs\n      cap\n      __typename\n    }\n    extLinkResp {\n      success\n      data\n      error\n      __typename\n    }\n    metaTxResp {\n      metaSig2\n      autoTaskUrl\n      metaSpaceAddr\n      forwarderAddr\n      metaTxHash\n      reqQueueing\n      __typename\n    }\n    solanaTxResp {\n      mint\n      updateAuthority\n      explorerUrl\n      signedTx\n      verifyID\n      __typename\n    }\n    aptosTxResp {\n      signatureExpiredAt\n      tokenName\n      __typename\n    }\n    tokenRewardCampaignTxResp {\n      signatureExpiredAt\n      verifyID\n      __typename\n    }\n    loyaltyPointsTxResp {\n      TotalClaimedPoints\n      __typename\n    }\n    flowTxResp {\n      Name\n      Description\n      Thumbnail\n      __typename\n    }\n    __typename\n  }\n}\n"
        }
        response = self.session.post('https://graphigo.prd.galaxy.eco/query', json=payload)

        if 'failed to verify recaptcha token' in response.text:
            logger.warning(f'[-] Galxe | Outdated `w` token! Dont stop this soft, just change it in `w.txt`')
            sleep(10)
            return self.claim()

        elif response.status_code == 200:
            if response.json()['data']['prepareParticipate']['disallowReason'] != "":
                raise Exception(f"[-] Galxe | Claim points error: {response.json()['data']['prepareParticipate']['disallowReason']}")

            elif response.json()['data']['prepareParticipate']['loyaltyPointsTxResp'] == None:
                logger.info(f'[+] Galxe | Already claimed points today')
                return f'✅ Already claimed points'

            total_points = response.json()['data']['prepareParticipate']['loyaltyPointsTxResp']['TotalClaimedPoints']
            logger.success(f'[+] Galxe | Claimed points: {total_points}')
            return f'✅ Claimed {total_points} points'
        else:
            logger.error(f'[-] Galxe | Claim points error: {response.status_code} {response.text}')
            retry += 1
            if retry >= self.max_retries: raise Exception(f"[-] Galxe | Claim points out of attempts: {response.text}")


    def get_campaign_detail(self):
        payload = {
            "operationName": "CampaignDetailAll",
            "variables": {
                "address": self.address,
                "id": "GCTN3ttM4T",
                "withAddress": True
            },
            "query": "query CampaignDetailAll($id: ID!, $address: String!, $withAddress: Boolean!) {\n  campaign(id: $id) {\n    ...CampaignForSiblingSlide\n    coHostSpaces {\n      ...SpaceDetail\n      isAdmin(address: $address) @include(if: $withAddress)\n      isFollowing @include(if: $withAddress)\n      followersCount\n      categories\n      __typename\n    }\n    bannerUrl\n    ...CampaignDetailFrag\n    userParticipants(address: $address, first: 1) @include(if: $withAddress) {\n      list {\n        status\n        premintTo\n        __typename\n      }\n      __typename\n    }\n    space {\n      ...SpaceDetail\n      isAdmin(address: $address) @include(if: $withAddress)\n      isFollowing @include(if: $withAddress)\n      followersCount\n      categories\n      __typename\n    }\n    isBookmarked(address: $address) @include(if: $withAddress)\n    inWatchList\n    claimedLoyaltyPoints(address: $address) @include(if: $withAddress)\n    parentCampaign {\n      id\n      isSequencial\n      thumbnail\n      __typename\n    }\n    isSequencial\n    numNFTMinted\n    childrenCampaigns {\n      ...ChildrenCampaignsForCampaignDetailAll\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment CampaignDetailFrag on Campaign {\n  id\n  ...CampaignMedia\n  ...CampaignForgePage\n  ...CampaignForCampaignParticipantsBox\n  name\n  numberID\n  type\n  inWatchList\n  cap\n  info\n  useCred\n  smartbalancePreCheck(mintCount: 1)\n  smartbalanceDeposited\n  formula\n  status\n  seoImage\n  creator\n  tags\n  thumbnail\n  gasType\n  isPrivate\n  createdAt\n  requirementInfo\n  description\n  enableWhitelist\n  chain\n  startTime\n  endTime\n  requireEmail\n  requireUsername\n  blacklistCountryCodes\n  whitelistRegions\n  rewardType\n  distributionType\n  rewardName\n  claimEndTime\n  loyaltyPoints\n  tokenRewardContract {\n    id\n    address\n    chain\n    __typename\n  }\n  tokenReward {\n    userTokenAmount\n    tokenAddress\n    depositedTokenAmount\n    tokenRewardId\n    tokenDecimal\n    tokenLogo\n    tokenSymbol\n    __typename\n  }\n  nftHolderSnapshot {\n    holderSnapshotBlock\n    __typename\n  }\n  spaceStation {\n    id\n    address\n    chain\n    __typename\n  }\n  ...WhitelistInfoFrag\n  ...WhitelistSubgraphFrag\n  gamification {\n    ...GamificationDetailFrag\n    __typename\n  }\n  creds {\n    id\n    name\n    type\n    credType\n    credSource\n    referenceLink\n    description\n    lastUpdate\n    lastSync\n    syncStatus\n    credContractNFTHolder {\n      timestamp\n      __typename\n    }\n    chain\n    eligible(address: $address, campaignId: $id)\n    subgraph {\n      endpoint\n      query\n      expression\n      __typename\n    }\n    dimensionConfig\n    value {\n      gitcoinPassport {\n        score\n        lastScoreTimestamp\n        __typename\n      }\n      __typename\n    }\n    commonInfo {\n      participateEndTime\n      modificationInfo\n      __typename\n    }\n    __typename\n  }\n  credentialGroups(address: $address) {\n    ...CredentialGroupForAddress\n    __typename\n  }\n  rewardInfo {\n    discordRole {\n      guildId\n      guildName\n      roleId\n      roleName\n      inviteLink\n      __typename\n    }\n    premint {\n      startTime\n      endTime\n      chain\n      price\n      totalSupply\n      contractAddress\n      banner\n      __typename\n    }\n    loyaltyPoints {\n      points\n      __typename\n    }\n    loyaltyPointsMysteryBox {\n      points\n      weight\n      __typename\n    }\n    __typename\n  }\n  participants {\n    participantsCount\n    bountyWinnersCount\n    __typename\n  }\n  taskConfig(address: $address) {\n    participateCondition {\n      conditions {\n        ...ExpressionEntity\n        __typename\n      }\n      conditionalFormula\n      eligible\n      __typename\n    }\n    rewardConfigs {\n      id\n      conditions {\n        ...ExpressionEntity\n        __typename\n      }\n      conditionalFormula\n      description\n      rewards {\n        ...ExpressionReward\n        __typename\n      }\n      eligible\n      rewardAttrVals {\n        attrName\n        attrTitle\n        attrVal\n        __typename\n      }\n      __typename\n    }\n    referralConfig {\n      id\n      conditions {\n        ...ExpressionEntity\n        __typename\n      }\n      conditionalFormula\n      description\n      rewards {\n        ...ExpressionReward\n        __typename\n      }\n      eligible\n      rewardAttrVals {\n        attrName\n        attrTitle\n        attrVal\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  referralCode(address: $address)\n  recurringType\n  latestRecurringTime\n  nftTemplates {\n    id\n    image\n    treasureBack\n    __typename\n  }\n  __typename\n}\n\nfragment CampaignMedia on Campaign {\n  thumbnail\n  rewardName\n  type\n  gamification {\n    id\n    type\n    __typename\n  }\n  __typename\n}\n\nfragment CredentialGroupForAddress on CredentialGroup {\n  id\n  description\n  credentials {\n    ...CredForAddressWithoutMetadata\n    __typename\n  }\n  conditionRelation\n  conditions {\n    expression\n    eligible\n    ...CredentialGroupConditionForVerifyButton\n    __typename\n  }\n  rewards {\n    expression\n    eligible\n    rewardCount\n    rewardType\n    __typename\n  }\n  rewardAttrVals {\n    attrName\n    attrTitle\n    attrVal\n    __typename\n  }\n  claimedLoyaltyPoints\n  __typename\n}\n\nfragment CredForAddressWithoutMetadata on Cred {\n  id\n  name\n  type\n  credType\n  credSource\n  referenceLink\n  description\n  lastUpdate\n  lastSync\n  syncStatus\n  credContractNFTHolder {\n    timestamp\n    __typename\n  }\n  chain\n  eligible(address: $address)\n  subgraph {\n    endpoint\n    query\n    expression\n    __typename\n  }\n  dimensionConfig\n  value {\n    gitcoinPassport {\n      score\n      lastScoreTimestamp\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment CredentialGroupConditionForVerifyButton on CredentialGroupCondition {\n  expression\n  eligibleAddress\n  __typename\n}\n\nfragment WhitelistInfoFrag on Campaign {\n  id\n  whitelistInfo(address: $address) {\n    address\n    maxCount\n    usedCount\n    claimedLoyaltyPoints\n    currentPeriodClaimedLoyaltyPoints\n    currentPeriodMaxLoyaltyPoints\n    __typename\n  }\n  __typename\n}\n\nfragment WhitelistSubgraphFrag on Campaign {\n  id\n  whitelistSubgraph {\n    query\n    endpoint\n    expression\n    variable\n    __typename\n  }\n  __typename\n}\n\nfragment GamificationDetailFrag on Gamification {\n  id\n  type\n  nfts {\n    nft {\n      id\n      animationURL\n      category\n      powah\n      image\n      name\n      treasureBack\n      nftCore {\n        ...NftCoreInfoFrag\n        __typename\n      }\n      traits {\n        name\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  airdrop {\n    name\n    contractAddress\n    token {\n      address\n      icon\n      symbol\n      __typename\n    }\n    merkleTreeUrl\n    addressInfo(address: $address) {\n      index\n      amount {\n        amount\n        ether\n        __typename\n      }\n      proofs\n      __typename\n    }\n    __typename\n  }\n  forgeConfig {\n    minNFTCount\n    maxNFTCount\n    requiredNFTs {\n      nft {\n        category\n        powah\n        image\n        name\n        nftCore {\n          capable\n          contractAddress\n          __typename\n        }\n        __typename\n      }\n      count\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment NftCoreInfoFrag on NFTCore {\n  id\n  capable\n  chain\n  contractAddress\n  name\n  symbol\n  dao {\n    id\n    name\n    logo\n    alias\n    __typename\n  }\n  __typename\n}\n\nfragment ExpressionEntity on ExprEntity {\n  cred {\n    id\n    name\n    type\n    credType\n    credSource\n    dimensionConfig\n    referenceLink\n    description\n    lastUpdate\n    lastSync\n    chain\n    eligible(address: $address)\n    metadata {\n      visitLink {\n        link\n        __typename\n      }\n      twitter {\n        isAuthentic\n        __typename\n      }\n      __typename\n    }\n    commonInfo {\n      participateEndTime\n      modificationInfo\n      __typename\n    }\n    __typename\n  }\n  attrs {\n    attrName\n    operatorSymbol\n    targetValue\n    __typename\n  }\n  attrFormula\n  eligible\n  eligibleAddress\n  __typename\n}\n\nfragment ExpressionReward on ExprReward {\n  arithmetics {\n    ...ExpressionEntity\n    __typename\n  }\n  arithmeticFormula\n  rewardType\n  rewardCount\n  rewardVal\n  __typename\n}\n\nfragment CampaignForgePage on Campaign {\n  id\n  numberID\n  chain\n  spaceStation {\n    address\n    __typename\n  }\n  gamification {\n    forgeConfig {\n      maxNFTCount\n      minNFTCount\n      requiredNFTs {\n        nft {\n          category\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment CampaignForCampaignParticipantsBox on Campaign {\n  ...CampaignForParticipantsDialog\n  id\n  chain\n  space {\n    id\n    isAdmin(address: $address)\n    __typename\n  }\n  participants {\n    participants(first: 10, after: \"-1\", download: false) {\n      list {\n        address {\n          id\n          avatar\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    participantsCount\n    bountyWinners(first: 10, after: \"-1\", download: false) {\n      list {\n        createdTime\n        address {\n          id\n          avatar\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    bountyWinnersCount\n    __typename\n  }\n  __typename\n}\n\nfragment CampaignForParticipantsDialog on Campaign {\n  id\n  name\n  type\n  rewardType\n  chain\n  nftHolderSnapshot {\n    holderSnapshotBlock\n    __typename\n  }\n  space {\n    isAdmin(address: $address)\n    __typename\n  }\n  rewardInfo {\n    discordRole {\n      guildName\n      roleName\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment SpaceDetail on Space {\n  id\n  name\n  info\n  thumbnail\n  alias\n  status\n  links\n  isVerified\n  discordGuildID\n  followersCount\n  nftCores(input: {first: 1}) {\n    list {\n      id\n      marketLink\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment ChildrenCampaignsForCampaignDetailAll on Campaign {\n  space {\n    ...SpaceDetail\n    isAdmin(address: $address) @include(if: $withAddress)\n    isFollowing @include(if: $withAddress)\n    followersCount\n    categories\n    __typename\n  }\n  ...CampaignDetailFrag\n  claimedLoyaltyPoints(address: $address) @include(if: $withAddress)\n  userParticipants(address: $address, first: 1) @include(if: $withAddress) {\n    list {\n      status\n      __typename\n    }\n    __typename\n  }\n  parentCampaign {\n    id\n    isSequencial\n    __typename\n  }\n  __typename\n}\n\nfragment CampaignForSiblingSlide on Campaign {\n  id\n  space {\n    id\n    alias\n    __typename\n  }\n  parentCampaign {\n    id\n    thumbnail\n    isSequencial\n    childrenCampaigns {\n      id\n      ...CampaignForGetImage\n      ...CampaignForCheckFinish\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment CampaignForCheckFinish on Campaign {\n  claimedLoyaltyPoints(address: $address)\n  whitelistInfo(address: $address) {\n    usedCount\n    __typename\n  }\n  __typename\n}\n\nfragment CampaignForGetImage on Campaign {\n  ...GetImageCommon\n  nftTemplates {\n    image\n    __typename\n  }\n  __typename\n}\n\nfragment GetImageCommon on Campaign {\n  ...CampaignForTokenObject\n  id\n  type\n  thumbnail\n  __typename\n}\n\nfragment CampaignForTokenObject on Campaign {\n  tokenReward {\n    tokenAddress\n    tokenSymbol\n    tokenDecimal\n    tokenLogo\n    __typename\n  }\n  tokenRewardContract {\n    id\n    chain\n    __typename\n  }\n  __typename\n}\n"
        }

        response = self.session.post('https://graphigo.prd.galaxy.eco/query', json=payload)
        if response.status_code == 200:
            tasks_to_do = {}
            all_tasks_id = []
            tasks_response = response.json()['data']['campaign']['credentialGroups'][0] # CHANGE IT FOR ANOTHER GALXE
            claimed_points = tasks_response['claimedLoyaltyPoints'] # 500
            credential_group_id = tasks_response['id'] # "2242090000"
            for task in tasks_response['credentials']:
                all_tasks_id.append(task["id"])
                if task["eligible"]: continue
                tasks_to_do[task["id"]] = {'type': task["credType"], 'id': tasks_response['credentials'].index(task)}

            return {'claimed_points': claimed_points, 'credential_group_id': credential_group_id, 'tasks_to_do': tasks_to_do, 'all_tasks_id': all_tasks_id}
        else:
            logger.error(f'[-] Galxe | Get points amount error: {response.status_code} {response.text}')
            sleep(5)


    def solve_geecaptcha(self):
        try:
            callback = 'geetest_' + str(round(random.uniform(0, 1) * 10000) + round(time() * 1000))

            response_ = self.session.get('https://gcaptcha4.geetest.com/load', params={
                'captcha_id': '244bcb8b9846215df5af4c624a750db4',
                'challenge': uuid4(),
                'client_type': 'web',
                'lang': 'ru-ru',
                'callback': callback,
            })
            response = loads(response_.text.split(f"{callback}(")[1][:-1])

            try:
                with open('./w.txt') as f: w = f.read()
            except:
                with open('../w.txt') as f: w = f.read()

            response2_ = self.session.get('https://gcaptcha4.geetest.com/verify', params={
                'captcha_id': '244bcb8b9846215df5af4c624a750db4',
                'client_type': 'web',
                'lot_number': response['data']['lot_number'],
                'payload': response['data']['payload'],
                'process_token': response['data']['process_token'],
                'payload_protocol': '1',
                'pt': '1',
                'w': w,
                callback: callback
            })
            if 'param decrypt error' in response2_.text:
                logger.warning(f'[-] Galxe | Bad `w` token! Dont stop this soft, just change it in `w.txt`')
                sleep(10)
                return self.solve_geecaptcha()
            response2 = loads(response2_.text[1:-1])

            return {
                "lotNumber": response2['data']['seccode']['lot_number'],
                "captchaOutput": response2['data']['seccode']['captcha_output'],
                "passToken": response2['data']['seccode']['pass_token'],
                "genTime": response2['data']['seccode']['gen_time']
            }
        except Exception as err:
            logger.warning(f'Couldnt get geecaptcha, trying again: {err}')
            sleep(5)
            return self.solve_geecaptcha()


    def send_email(self, email: str):
        payload = {
            "operationName": "SendVerifyCode",
            "variables": {
                "input": {
                    "address": self.address,
                    "email": email,
                    "captcha": self.solve_geecaptcha()
                }
            },
            "query": "mutation SendVerifyCode($input: SendVerificationEmailInput!) {\n  sendVerificationCode(input: $input) {\n    code\n    message\n    __typename\n  }\n}\n"
        }
        r = self.session.post('https://graphigo.prd.galaxy.eco/query', json=payload)

        if 'failed to verify recaptcha token' in r.text:
            logger.warning(f'[-] Galxe | Outdated `w` token! Dont stop this soft, just change it in `w.txt`')
            sleep(10)
            return self.send_email(email=email)
        elif r.json() == {"data": {"sendVerificationCode": None}}:
            return True
        else:
            logger.warning(f'[-] Galxe | Cannot send email from Galxe to {email} error: {r.text}')
            sleep(10)
            return self.send_email(email=email)


    def confirm_email(self, email: str, code: str):
        payload = {
            "operationName": "UpdateEmail",
            "variables": {
                "input": {
                    "address": self.address,
                    "email": email,
                    "verificationCode": code
                }
            },
            "query": "mutation UpdateEmail($input: UpdateEmailInput!) {\n  updateEmail(input: $input) {\n    code\n    message\n    __typename\n  }\n}\n"
        }
        r = self.session.post('https://graphigo.prd.galaxy.eco/query', json=payload)

        if r.json() == {"data": {"updateEmail": None}}:
            logger.info(f'[+] Galxe | Email {email} successfully bound')
            return True
        elif 'InvalidArgument desc = Wrong code, please try again' in r.text:
            raise Exception(f'[-] Galxe | Email "{email}" already bound with another account')
        else:
            logger.warning(f'[-] Galxe | Cannot bind email {email} error: {r.text}')
            sleeping(10)
            return self.confirm_email(email=email, code=code)


    def open_faucet(self):
        payload = {
            "operationName": "AddTypedCredentialItems",
            "variables": {
                "input": {
                    "credId": "367886459336302592",
                    "campaignId": "GCTN3ttM4T",
                    "operation": "APPEND",
                    "items": [self.address],
                    "captcha": self.solve_geecaptcha()
                }
            },
            "query": "mutation AddTypedCredentialItems($input: MutateTypedCredItemInput!) {\n  typedCredentialItems(input: $input) {\n    id\n    __typename\n  }\n}\n"
        }
        r = self.session.post('https://graphigo.prd.galaxy.eco/query', json=payload)

        if 'failed to verify recaptcha token' in r.text:
            logger.warning(f'[-] Galxe | Outdated `w` token! Dont stop this soft, just change it in `w.txt`')
            sleep(10)
            return self.open_faucet()
        elif r.json() != {"data": {"typedCredentialItems": {"id": "367886459336302592","__typename": "Cred"}}}:
            logger.warning(f'Cant open faucet quest on Galxe')
            sleep(10)
            return self.open_faucet()


    def solve_2captcha(self):
        def create_task():
            proxy_type, user, psw, ip, port = settings.PROXY.replace('://', ':').replace('@', ':').split(':')
            payload = {
                "clientKey": settings.CAPTCHA_KEY,
                "task": {
                    "type": "RecaptchaV3Task",
                    "websiteURL": "https://artio.faucet.berachain.com/",
                    "websiteKey": '6LfOA04pAAAAAL9ttkwIz40hC63_7IsaU2MgcwVH',
                    "pageAction": "submit",
                    "userAgent": self.session.headers['User-Agent'],
                    "proxy": f"{proxy_type}:{ip}:{port}:{user}:{psw}",
                    "minScore": 0.9,
                    # "isInvisible": True
                }
            }
            r = requests.post(f'https://{api_url}/createTask', json=payload)
            if r.json().get('taskId'):
                return r.json()['taskId']
            else:
                raise Exception(f'[-] Faucet | Captcha error: {r.text}')

        def get_task_result(task_id: str):
            payload = {
                "clientKey": settings.CAPTCHA_KEY,
                "taskId": task_id
            }
            r = requests.post(f'https://{api_url}/getTaskResult', json=payload)

            if r.json().get('status') in ['pending', 'processing']:
                sleep(3)
                return get_task_result(task_id=task_id)
            elif r.json().get('status') == 'ready':
                logger.info(f'[+] Faucet | Captcha solved')
                return r.json()['solution']['gRecaptchaResponse']
            else:
                raise Exception(f'[-] Faucet | Couldnt solve captcha: {r.text}')

        api_url = 'api.capsolver.com'
        task_id = create_task()
        logger.info(f'[•] Faucet | Waiting for solve captcha')
        return get_task_result(task_id=task_id)


    def request_faucet(self, address: str):
        captcha_response = self.solve_2captcha()

        payload = {"address": address}
        url = f'https://artio-80085-faucet-api-recaptcha.berachain.com/api/claim?address={address}'
        self.session.headers.update({
            'Authorization': f'Bearer {captcha_response}',
            'Origin': 'https://artio.faucet.berachain.com',
            'Referer': 'https://artio.faucet.berachain.com/',
        })

        r = self.session.post(url, json=payload)
        del self.session.headers['Authorization']

        if r.status_code == 200 and r.json().get('msg'):
            logger.success(f'[+] Faucet | BERA tokens requested: {r.json()["msg"]}')
        elif 'You have exceeded the rate limit' in r.text:
            raise Exception(f'[-] Faucet | {r.text.strip()}')
        elif '503 Service Temporarily Unavailable' in r.text:
            logger.warning(f'[-] Faucet | BERA Faucet is not working now, waiting when it will be available')
            while True:
                r = self.session.post(url, json=payload)
                if '503 Service Temporarily Unavailable' in r.text:
                    sleep(10)
                else: return self.request_faucet(address=address)
        else:
            logger.warning(f'[-] Faucet | Couldnt request BERA tokens: {r.status_code} {r.text.strip()}')
            return self.request_faucet(address=address)


    def quote_swap(self, value_to_swap: int):
        self.session.headers.update({
            'Origin': 'https://artio.bex.berachain.com',
            'Referer': 'https://artio.bex.berachain.com/'
        })
        params = {
            'quoteAsset': '0x6581e59A1C8dA66eD0D313a0d4029DcE2F746Cc5',
            'baseAsset': '0x5806E416dA447b267cEA759358cF22Cc41FAE80F',
            'amount': value_to_swap,
            'swap_type': 'given_in',
        }
        r = self.session.get('https://artio-80085-dex-router.berachain.com/dex/route', params=params)
        return r.json()['steps'][0]

