<template>
  <div class="knowledge-search">
    <a-card title="知识库检索" :bordered="false">
      <!-- 搜索参数 -->
      <div class="search-params">
        <a-row :gutter="16">
          <a-col :span="16">
            <a-input
              v-model:value="searchQuery"
              placeholder="请输入检索关键词..."
              size="large"
              @keydown.enter="performSearch"
            >
              <template #prefix>
                <SearchOutlined />
              </template>
            </a-input>
          </a-col>
          <a-col :span="4">
            <a-input-number
              v-model:value="topK"
              placeholder="结果数量"
              :min="1"
              :max="20"
              size="large"
              style="width: 100%"
            />
          </a-col>
          <a-col :span="4">
            <a-button
              type="primary"
              size="large"
              :loading="searching"
              @click="performSearch"
              style="width: 100%"
            >
              检索
            </a-button>
          </a-col>
        </a-row>
        
        <a-row :gutter="16" style="margin-top: 16px">
          <a-col :span="8">
            <a-slider
              v-model:value="threshold"
              :min="0"
              :max="1"
              :step="0.1"
              :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
              tooltip-formatter="(value) => `${value}`"
            />
            <div class="slider-label">相似度阈值: {{ threshold }}</div>
          </a-col>
          <a-col :span="8">
            <a-space>
              <a-checkbox v-model:checked="useTextSearch">使用纯文本检索</a-checkbox>
              <a-checkbox v-model:checked="autoSearch">自动检索</a-checkbox>
            </a-space>
          </a-col>
          <a-col :span="8">
            <a-space>
              <a-button size="small" @click="clearSearch">清空</a-button>
              <a-button size="small" @click="exportResults">导出结果</a-button>
            </a-space>
          </a-col>
        </a-row>
      </div>
      
      <!-- 搜索历史 -->
      <div v-if="searchHistory.length > 0" class="search-history">
        <a-divider orientation="left">搜索历史</a-divider>
        <a-space wrap>
          <a-tag
            v-for="(item, index) in searchHistory"
            :key="index"
            class="history-tag"
            @click="useHistoryQuery(item)"
          >
            {{ item }}
          </a-tag>
        </a-space>
      </div>
      
      <!-- 搜索结果 -->
      <div v-if="searchResults.length > 0" class="search-results">
        <a-divider orientation="left">
          搜索结果 ({{ searchResults.length }})
          <a-tag color="blue" style="margin-left: 8px">
            相似度阈值: {{ threshold }}
          </a-tag>
        </a-divider>
        
        <a-list
          :data-source="searchResults"
          :pagination="pagination"
          item-layout="vertical"
        >
          <template #renderItem="{ item, index }">
            <a-list-item>
              <a-card size="small" :bordered="false" style="width: 100%">
                <template #title>
                  <a-space>
                    <span>结果 #{{ index + 1 }}</span>
                    <a-tag v-if="item.score" color="green">
                      相似度: {{ (item.score * 100).toFixed(1) }}%
                    </a-tag>
                  </a-space>
                </template>
                
                <template #extra>
                  <a-space>
                    <a-button 
                      type="link" 
                      size="small" 
                      @click="copyContent(item.content)"
                    >
                      复制
                    </a-button>
                    <a-button 
                      type="link" 
                      size="small" 
                      @click="askAboutContent(item.content)"
                    >
                      询问详情
                    </a-button>
                  </a-space>
                </template>
                
                <div class="result-content">
                  <div class="content-text" v-html="formatContent(item.content)"></div>
                  
                  <div v-if="item.metadata" class="metadata">
                    <a-divider />
                    <a-descriptions size="small" :column="3">
                      <a-descriptions-item 
                        v-for="(value, key) in item.metadata" 
                        :key="key"
                        :label="key"
                      >
                        {{ value }}
                      </a-descriptions-item>
                    </a-descriptions>
                  </div>
                </div>
              </a-card>
            </a-list-item>
          </template>
        </a-list>
      </div>
      
      <!-- 无结果提示 -->
      <div v-else-if="hasSearched && !searching" class="no-results">
        <a-empty
          description="未找到相关结果"
          :image="Empty.PRESENTED_IMAGE_SIMPLE"
        >
          <template #extra>
            <a-space>
              <a-button type="primary" @click="adjustSearchParams">
                调整搜索参数
              </a-button>
              <a-button @click="clearSearch">重新搜索</a-button>
            </a-space>
          </template>
        </a-empty>
      </div>
      
      <!-- 搜索统计 -->
      <div v-if="searchStats" class="search-stats">
        <a-divider />
        <a-row :gutter="16">
          <a-col :span="6">
            <a-statistic title="搜索次数" :value="searchStats.totalSearches" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="平均响应时间" :value="searchStats.avgResponseTime" suffix="ms" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="成功率" :value="searchStats.successRate" suffix="%" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="总结果数" :value="searchStats.totalResults" />
          </a-col>
        </a-row>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { message } from 'ant-design-vue';
import { SearchOutlined } from '@ant-design/icons-vue';
import { Empty } from 'ant-design-vue';
import { search, searchText } from '../api/external-rag.api';
import { SearchParams, SearchResult } from '../data/external-rag.data';

const searchQuery = ref('');
const topK = ref(5);
const threshold = ref(0.7);
const useTextSearch = ref(false);
const autoSearch = ref(false);
const searching = ref(false);
const hasSearched = ref(false);

const searchResults = ref<SearchResult['results']>([]);
const searchHistory = ref<string[]>([]);
const searchStats = ref({
  totalSearches: 0,
  avgResponseTime: 0,
  successRate: 100,
  totalResults: 0
});

// 分页配置
const pagination = computed(() => ({
  pageSize: 5,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条结果`
}));

// 执行搜索
const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    message.warning('请输入搜索关键词');
    return;
  }
  
  try {
    searching.value = true;
    hasSearched.value = true;
    const startTime = Date.now();
    
    let response;
    if (useTextSearch.value) {
      response = await searchText(searchQuery.value.trim());
      // 纯文本搜索返回的是字符串，需要转换格式
      searchResults.value = [{
        content: response,
        score: 1.0
      }];
    } else {
      response = await search({
        query: searchQuery.value.trim(),
        topK: topK.value,
        threshold: threshold.value
      });
      
      if (response.code === 200) {
        searchResults.value = [{
          content: response.data.response,
          score: 1.0
        }];
      } else {
        throw new Error(response.msg);
      }
    }
    
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    
    // 更新搜索历史
    if (!searchHistory.value.includes(searchQuery.value.trim())) {
      searchHistory.value.unshift(searchQuery.value.trim());
      if (searchHistory.value.length > 10) {
        searchHistory.value.pop();
      }
    }
    
    // 更新统计信息
    searchStats.value.totalSearches++;
    searchStats.value.totalResults += searchResults.value.length;
    searchStats.value.avgResponseTime = Math.round(
      (searchStats.value.avgResponseTime * (searchStats.value.totalSearches - 1) + responseTime) / searchStats.value.totalSearches
    );
    
    message.success(`搜索完成，找到 ${searchResults.value.length} 条结果`);
    
  } catch (error) {
    message.error('搜索失败: ' + error);
    searchResults.value = [];
  } finally {
    searching.value = false;
  }
};

// 使用历史查询
const useHistoryQuery = (query: string) => {
  searchQuery.value = query;
  if (autoSearch.value) {
    performSearch();
  }
};

// 清空搜索
const clearSearch = () => {
  searchQuery.value = '';
  searchResults.value = [];
  hasSearched.value = false;
};

// 导出结果
const exportResults = () => {
  if (searchResults.value.length === 0) {
    message.warning('没有搜索结果可导出');
    return;
  }
  
  const content = searchResults.value
    .map((result, index) => `结果 #${index + 1}:\n${result.content}`)
    .join('\n\n');
  
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `TrustRAG搜索结果_${searchQuery.value}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
  a.click();
  URL.revokeObjectURL(url);
  message.success('搜索结果导出成功');
};

// 复制内容
const copyContent = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content);
    message.success('内容已复制到剪贴板');
  } catch (error) {
    message.error('复制失败');
  }
};

// 询问详情
const askAboutContent = (content: string) => {
  // 这里可以触发聊天功能，将内容作为上下文
  message.info('功能开发中：将集成聊天功能');
};

// 调整搜索参数
const adjustSearchParams = () => {
  threshold.value = Math.max(0, threshold.value - 0.1);
  topK.value = Math.min(20, topK.value + 2);
  message.info('已调整搜索参数，请重新搜索');
};

// 格式化内容
const formatContent = (content: string) => {
  return content.replace(/\n/g, '<br>');
};

// 监听自动搜索
watch(autoSearch, (newVal) => {
  if (newVal && searchQuery.value.trim()) {
    performSearch();
  }
});

// 监听阈值变化
watch(threshold, () => {
  if (autoSearch.value && searchQuery.value.trim()) {
    performSearch();
  }
});
</script>

<style scoped>
.knowledge-search {
  height: 100%;
}

.search-params {
  margin-bottom: 24px;
}

.slider-label {
  text-align: center;
  margin-top: 8px;
  color: #666;
}

.search-history {
  margin-bottom: 24px;
}

.history-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.history-tag:hover {
  background-color: #1890ff;
  color: white;
}

.search-results {
  margin-bottom: 24px;
}

.result-content {
  margin-top: 16px;
}

.content-text {
  line-height: 1.6;
  margin-bottom: 16px;
}

.metadata {
  margin-top: 16px;
}

.no-results {
  text-align: center;
  padding: 40px 0;
}

.search-stats {
  margin-top: 24px;
}

:deep(.ant-list-item) {
  padding: 16px 0;
}

:deep(.ant-card-head) {
  min-height: auto;
  padding: 12px 16px;
}

:deep(.ant-card-body) {
  padding: 16px;
}
</style>
