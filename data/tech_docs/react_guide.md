# React 官方文档精要

## 核心概念

React 是一个用于构建用户界面的 JavaScript 库。它采用组件化的开发模式，通过声明式语法描述 UI 状态。

### JSX

JSX 是 JavaScript 的语法扩展，允许在 JS 中编写类似 HTML 的标记：

```jsx
function Greeting({ name }) {
  return <h1>Hello, {name}!</h1>;
}
```

JSX 会被 Babel 编译为 `React.createElement()` 调用。

### 组件与 Props

组件是 React 应用的基本构建块。组件接受 props（属性）作为输入，返回 React 元素。

```jsx
function Welcome(props) {
  return <h1>Hello, {props.name}</h1>;
}
```

组件名必须以大写字母开头。Props 是只读的，组件不能修改自己的 props。

### State 与生命周期

State 是组件的私有数据，用于管理随时间变化的状态。

**useState Hook：**
```jsx
const [count, setCount] = useState(0);
```

**useEffect Hook：**
```jsx
useEffect(() => {
  document.title = `You clicked ${count} times`;
  return () => { /* cleanup */ };
}, [count]);
```

第二个参数是依赖数组：空数组表示仅在挂载时运行，不传则表示每次渲染后都运行。

### Hooks 规则

1. 只在函数组件顶层调用 Hooks
2. 只在 React 函数组件或自定义 Hook 中调用 Hooks
3. 自定义 Hook 必须以 `use` 开头

### 条件渲染

```jsx
{isLoggedIn ? <UserDashboard /> : <LoginPage />}
{unreadMessages.length > 0 && <Badge count={unreadMessages.length} />}
```

### 列表与 Key

```jsx
const items = todos.map(todo =>
  <li key={todo.id}>{todo.text}</li>
);
```

key 帮助 React 识别哪些元素变化了，应当使用稳定的唯一标识符，避免使用数组索引。

## 高级特性

### Context API

用于全局共享数据（如主题、用户认证），避免 props 逐层传递：

```jsx
const ThemeContext = React.createContext('light');

function App() {
  return (
    <ThemeContext.Provider value="dark">
      <Toolbar />
    </ThemeContext.Provider>
  );
}

function Toolbar() {
  const theme = useContext(ThemeContext);
  return <div className={theme}>...</div>;
}
```

### useReducer

适用于复杂状态逻辑，尤其是涉及多个子值或下个状态依赖前一个状态：

```jsx
const [state, dispatch] = useReducer(reducer, initialState);
```

### useMemo 与 useCallback

`useMemo` 缓存计算结果，`useCallback` 缓存函数引用：

```jsx
const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);
const memoizedCallback = useCallback(() => doSomething(a, b), [a, b]);
```

仅在性能优化需要时使用，不要过早优化。

### useRef

用于访问 DOM 元素或保存可变值（不触发重新渲染）：

```jsx
const inputRef = useRef(null);
useEffect(() => { inputRef.current.focus(); }, []);
return <input ref={inputRef} />;
```

### Error Boundaries

类组件中实现 `componentDidCatch` 或 `static getDerivedStateFromError` 来捕获子组件树中的 JS 错误。

## React 18+ 新特性

### Concurrent Mode（并发模式）

React 18 引入并发特性，允许 React 中断渲染以处理更高优先级的更新。

### 自动批处理

React 18 中，所有状态更新都会自动批处理，包括在 Promise、setTimeout 中的更新。

### Suspense 改进

```jsx
<Suspense fallback={<Loading />}>
  <LazyComponent />
</Suspense>
```

React 18 支持服务端渲染中的 Suspense。

### useTransition 和 useDeferredValue

```jsx
const [isPending, startTransition] = useTransition();
const deferredValue = useDeferredValue(inputValue);
```

用于区分紧急更新和非紧急更新，提升用户体验。

## 推荐模式

1. **组合优于继承**：通过 children prop 或 render prop 复用代码
2. **状态提升**：将共享状态提升到最近的公共祖先
3. **不可变数据**：使用扩展运算符或 immer 更新 state 对象
4. **受控组件**：表单元素的值由 React state 控制
