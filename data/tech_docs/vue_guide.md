# Vue.js 官方文档精要

## 核心概念

Vue.js 是一套用于构建用户界面的渐进式 JavaScript 框架。它的核心库只关注视图层，通过丰富的生态系统支持构建复杂单页应用。

### 响应式基础

Vue 3 使用 Proxy 实现响应式系统，替代了 Vue 2 的 Object.defineProperty。

**ref()：** 用于基本类型和对象，需要通过 `.value` 访问
```js
import { ref } from 'vue'
const count = ref(0)
count.value++  // 触发响应式更新
```

**reactive()：** 用于对象类型，直接访问属性
```js
import { reactive } from 'vue'
const state = reactive({ count: 0 })
state.count++  // 自动追踪
```

reactive 的局限：不能替换整个对象、解构会丢失响应性。推荐使用 ref() 作为主要 API。

### 计算属性 computed

```js
const fullName = computed(() => `${firstName.value} ${lastName.value}`)
```

计算属性会缓存结果，只有依赖变化时才重新计算。应避免在计算属性中产生副作用。

### 侦听器 watch 与 watchEffect

```js
watch(count, (newVal, oldVal) => {
  console.log(`count changed from ${oldVal} to ${newVal}`)
})

watchEffect(() => {
  console.log(`count is: ${count.value}`)
})
```

watchEffect 自动追踪回调中访问的所有响应式依赖，立即执行一次。

### 模板语法

```html
<!-- 文本插值 -->
<span>{{ message }}</span>

<!-- 属性绑定 -->
<div :id="dynamicId" :class="{ active: isActive }"></div>

<!-- 条件渲染 -->
<h1 v-if="show">Hello</h1>
<h2 v-else-if="condition">World</h2>
<h3 v-else>Goodbye</h3>

<!-- 列表渲染 -->
<li v-for="item in items" :key="item.id">{{ item.text }}</li>

<!-- 事件处理 -->
<button @click="handleClick">Click</button>

<!-- 双向绑定 -->
<input v-model="text" />
```

## 组件系统

### Props 和 Emits

```js
// 子组件
const props = defineProps({
  title: { type: String, required: true }
})
const emit = defineEmits(['update', 'delete'])

emit('update', newValue)
```

### 插槽 Slots

```html
<!-- 默认插槽 -->
<slot />

<!-- 具名插槽 -->
<slot name="header" />

<!-- 作用域插槽 -->
<slot :item="item" :index="index" />
```

## Composition API vs Options API

Vue 3 推荐使用 Composition API（`<script setup>`），相比 Options API 有以下优势：

1. **更好的逻辑复用**：通过组合函数（composables）替代 mixins
2. **更灵活的组织**：相关逻辑可以放在一起
3. **更好的类型推导**：TypeScript 支持更完善
4. **更小的生产包**：`<script setup>` 代码可以被更好地 tree-shaking

### 自定义组合函数

```js
// useCounter.js
export function useCounter(initialValue = 0) {
  const count = ref(initialValue)
  const increment = () => count.value++
  const decrement = () => count.value--
  return { count, increment, decrement }
}
```

命名约定：组合函数必须以 `use` 开头。

## 路由与状态管理

### Vue Router 4

```js
const routes = [
  { path: '/', component: Home },
  { path: '/about', component: About, meta: { requiresAuth: true } },
  { path: '/user/:id', component: User }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})
```

支持动态路由匹配、嵌套路由、导航守卫。

### Pinia（状态管理）

```js
import { defineStore } from 'pinia'

export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubleCount = computed(() => count.value * 2)
  const increment = () => { count.value++ }
  return { count, doubleCount, increment }
})
```

Pinia 是 Vue 3 官方推荐的状态管理库，替代 Vuex。支持模块化、TypeScript、DevTools。

## 内置组件

### Transition

```html
<Transition name="fade">
  <p v-if="show">hello</p>
</Transition>
```

提供进入/离开过渡动画，支持 CSS 和 JS 动画。

### Teleport

```html
<Teleport to="body">
  <Modal />
</Teleport>
```

将组件渲染到 DOM 中的其他位置，常用于模态框、通知等。

### KeepAlive

```html
<KeepAlive>
  <component :is="activeComponent" />
</KeepAlive>
```

缓存组件实例，避免重复创建/销毁。

### Suspense（实验性）

```html
<Suspense>
  <AsyncComponent />
  <template #fallback>Loading...</template>
</Suspense>
```

协调异步依赖，展示加载状态。
