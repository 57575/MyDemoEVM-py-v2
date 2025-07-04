# I. Getting Started

1. Open the terminal, navigate to the project root directory, and enter the command `pip install -r requirements.txt` to install the dependencies.
2. Execute test cases: Use the `pytest` command in the terminal to run all unit tests, or configure the test path to `vm` in the IDE and then run the tests.
3. Write other transaction code, and then use the `execute_bytecode` method in the `vm.__init__.py` file to execute the transaction.

# II. Project Structure

This simple Ethereum Virtual Machine is divided into 3 modules. The first part is the machine state, and the main implementation classes are `State.py` and `Computation.py`. The second part is the implementation of Opcode logic, mainly implemented by the methods in the `logic` module. The third part is unit testing. The project has implemented at least one test case for the state database and each Opcodes.

## 2.1 Virtual Machine State

### 2.1.1 Computation

Computation is responsible for calculations. It manages the stack, memory, logs, and errors. The read and write interfaces for these four parts are also exposed to the Opcodes through Computation.

All expected runtime errors, such as insufficient stack, invalid opcode, and incorrect memory read/write positions, will cause the Computation to be interrupted and the machine state to be rolled back. The relevant error information will be stored in `computation.error`. For specific examples, you can refer to `test_opcodes_system.py` `test_invalid` function.

### 2.1.2 State

State is responsible for managing account information, block information, and the state database.
Block information is obtained through the public API, which is implemented in `EthereumAPI.py`.
Both account information and the state database are managed by the `AccountDB` class.
In particular, since transient storage was added after the CANCUN hard fork, it is directly managed by the `State` class.

#### 2.1.2.1 AccountDB

1. All code related to the state database is stored in the `/vm/db/..` directory.
2. All disk storage of the state database is managed by the Sqlite database. The data model definition of Sqlite is in `StateDBModel.py`.
3. All transaction management of the state database is implemented by the classes in `/vm/db/..`. This includes the encapsulation of the Sqlite interface, checkpoint management, persistence, and revert.
4. Since simulating smart contract execution does not require interaction with the main chain, to simplify the implementation, all Merkle Patricia tree implementations are omitted, so a correct storageRoot cannot be generated.
5. `AccountDB` is mainly responsible for managing three data models.
   - The first is `_account_stores`, which is responsible for managing a key - value storage database for each account. The implementation classes are `AccountStorageDB` -> `AccountBatchDB`. Among them, `AccountBatchDB` is responsible for interacting with the Sqlite database and transaction management, and `AccountStorageDB` exposes the interface to `AccountDB`.
   - The second is `_journaldb`, which is responsible for managing the mapping between smart contract code and its code hash. The implementation class is `CodeBatchDB`.
   - The third is `_journaltrie`, which is responsible for managing the mapping between accounts and the RLP - encoded account information. The implementation class is `AccountInfoBatchDB`.

#### 2.1.2.2 Transient Storage

Transient storage is responsible for managing temporary data, so it simply uses the `Memory DB` class for storage, with the underlying being a Python `Dict[bytes, bytes]`.

## 2.2 Opcodes

All Opcode logic is implemented in `/vm/logic/..`. Currently, the implemented Opcodes are consistent with the CANCUN hard fork. The file naming is based on the Opcode grouping. You can refer to the official Ethereum documentation: https://www.evm.codes/?fork=cancun

1. Since we are not concerned about the change in gas fees, although the gas fees for all Opcodes have been defined, they are not actually consumed during execution.
2. The changes introduced by EIP - 2929 only affect the calculation of gas fees and do not affect the actual logic, so they are not implemented.
3. The logic of predefined smart contracts is implemented in `/vm/precompiles/..`.

## 2.3 Unit Testing

Unit tests are all implemented in `/vm/test/..`.

1. All tests for the state database are stored in the directory `/vm/test/db/..`. This includes tests for `AccountDB`, `AccountBatchDB`, `AccountInfoBatchDB`, `CodeBatchDB`, and `TransientBatchDB`.
2. All unit tests for Opcodes are named `test_opcodes_*`, and the unit test file names correspond one - to - one with the files where the Opcode logic is located in the `/vm/logic/..` directory.
3. The unit test logic for Opcodes is mostly one of the following two:
   1. For simple Opcodes that do not require context, directly use the interfaces exposed by the `Computation` class to write data to the stack or memory and then perform operations. For example, `test_addmod`.
   2. For complex Opcodes that require context, use string concatenation to combine opcodes and data (for ease of reading, Opcode mnemonics are used during concatenation, and the actual concatenation result is bytecode, all in hexadecimal). Then, construct a `Computation` object to execute the bytecode, and finally check whether the results produced by `Computation` meet the expectations. For example, `test_create2` and `test_simple_loop`.
4. The general testing process is implemented in `test_opcode_arithmetic.py`. First, call the public API to obtain block information (the `create_execution_context` method). Then, initialize the virtual machine state based on the execution context content (the `build_state` method). After attaching necessary information (such as setting the balance or code for an account), finally use the `run_computation` method to run the code.

### Tips

1. Since the public API used has rate limits, running all unit tests at once may fail due to a failed call to the public API.

# 一、开始

1. 打开终端，进入项目根目录，输入`pip install -r requirements.txt`命令安装依赖。
2. 执行测试用例：在终端中使用`pytest`命令运行所有单元测试，或是在 IDE 中配置测试路径为 vm 然后运行。
3. 编写其它 transaction 代码，然后使用`vm.__init__.py`文件中的`execute_bytecode`方法执行 transaction

# 二、项目结构

这个简单的以太坊虚拟机分为 3 个模块。第一部分是虚拟机状态, 主要实现类为 `State.py` 和 `Computation.py`。第二部分为 Opcodes 逻辑实现，主要实现为 logic 模块中的方法。第三部分为单元测试，项目为 statedb 和所有 Opcodes 都实现了至少一个测试用例。

## 2.1 虚拟机状态

### 2.1.1 Computation

Computation 负责计算，它管理 stack、memory、log 和 error。这 4 部分的读写接口也通过 Computation 暴露给 Opcodes。

所有可预期的运行时错误，比如栈不足、无效操作码、错误的 memory 读写位置，会导致 Computation 被打断，然后执行状态回滚。相关的错误信息会存储在 Computation.error 中。具体例子可以查看 test_opcodes_system.py 中的 test_invalid

### 2.1.2 State

State 负责管理账户信息，Block 信息和 StateDB。  
Block 信息通过公共 API 获取，实现于 `EthereumAPI.py`。  
账户信息和 StateDB 均由 AccountDB 类管理。  
特别的，由于 transient storage 在 CANCUN 硬分叉之后才添加，所以它直接由 State 类管理。

#### 2.1.2.1 AccountDB

1. 所有 StateDB 相关的代码均存储于`/vm/db/..`目录。
2. 所有 StateDB 的硬盘存储均由 Sqlite 数据库负责管理。Sqlite 数据模型的定义为 `StateDBModel.py`。
3. 所有 StateDB 的事务管理均由`/vm/db/..`中的类实现。即包括 Sqlite 接口的封装、检查点管理、持久化和回滚。
4. 由于模拟智能合约执行无需和主链交互，为了简化实现，省略了所有 Merkle Patricia tree 的实现，因此无法生成正确的 storageRoot。
5. AccountDB 中主要负责管理三个数据模型。
   - 第一个是`_account_stores`,负责为每个账户管理一个 key-value 存储数据库。实现类为`AccountStorageDB`->`AccountBatchDB`。其中`AccountBatchDB`负责与 Sqlite 数据库交互和事务管理。`AccountStorageDB`向`AccountDB`暴露接口。
   - 第二个是`_journaldb`,负责管理智能合约代码和它的 code hash 之间的映射。实现类为`CodeBatchDB`。
   - 第三个是`_journaltrie`,负责管理账户和经过 rlp 编码后的账户信息之间的映射。实现类为`AccountInfoBatchDB`

#### 2.1.2.2 Transient Storage

transient storage 负责管理临时数据，因此简单的采用`Memory DB`类进行存储，底层是 python 的`Dict[bytes, bytes]`

## 2.2 Opcodes

所有的 Opcodes 逻辑均实现于`/vm/logic/..`中，目前实现的 Opcodes 与 CANCUN 硬分叉保持一致。文件的命名以 Opcodes 分组为依据。可以参考以太坊官方文档：https://www.evm.codes/?fork=cancun

1. 因为不关注 gas fee 的变化，因此虽然所有的 Opcodes gas fee 已定义，但是执行过程中未实际消耗。
2. EIP-2929 所产生的变化只影响 gas fee 的计算，不影响实际逻辑，因此并未实现。
3. 预定义智能合约的逻辑实现于`/vm/precompiles/..`中

## 2.3 单元测试

单元测试均实现于`/vm/test/..`中。

1. 所有对 StateDB 的测试都存放在目录`/vm/test/db/..`中。包括对`AccountDB`、`AccountBatchDB`、`AccountInfoBatchDB`、`CodeBatchDB`和`TransientBatchDB`的测试。
2. 所有对 Opcodes 的单元测试都以`test_opcodes_*`命名，单元测试文件名与`/vm/logic/..`目录中的 Opcodes 逻辑所处文件一一对应。
3. 对 Opcodes 的单元测试逻辑大多为以下两者之一：
   1. 简单、无需上下文的 Opcodes，直接使用 Computation 类暴露的接口向 stack 或是 memory 写入数据后进行运算。如`test_addmod`
   2. 负责、需要上下文的 Opcodes，使用字符串拼接操作码和数据后（为了方便阅读,拼接时使用的是 Opcodes 助记符,实际拼接结果为 Bytecode, 均为 16 进制数），构建 Computation 执行字节码，最后检查 Computation 产生的结果是否符合预期。如`test_create2`、`test_simple_loop`
4. 测试的通用流程实现于`test_opcode_arithmetic.py`中，首先调用公共 API 获取区块信息(`create_execution_context`方法)，然后通过执行上下文内容初始化虚拟机状态(`build_state`方法)，附加必要的信息（如为账户设置 balance 或 code）之后，最后使用`run_computation`方法运行代码。

### Tips

1. 由于使用的公共 API 有流量限制，因此一次性运行所有的单元测试可能会因为调用公共 API 失败而失败。
