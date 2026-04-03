#include <stdio.h>
#include <stdbool.h>

#define MAX_NODES 30
#define INF 9999

// 图的结构体
typedef struct {
    int numNodes; // 顶点数
    int adjacencyMatrix[MAX_NODES][MAX_NODES]; // 邻接矩阵
} Graph;

// 初始化图
void initGraph(Graph* graph, int numNodes) {
    graph->numNodes = numNodes;

    // 初始化邻接矩阵
    for (int i = 0; i < numNodes; i++) {
        for (int j = 0; j < numNodes; j++) {
            graph->adjacencyMatrix[i][j] = INF;
        }
    }
}

//初始化路径图
void initGraph1(Graph* graph, Graph* graph1, int numNodes) {
    graph1->numNodes = numNodes;

    // 初始化邻接矩阵
    for (int i = 0; i < numNodes; i++) {
        for (int j = 0; j < numNodes; j++) {
        	if(graph->adjacencyMatrix[i][j]!=INF){
        		graph1->adjacencyMatrix[i][j] = 1;
			}else{
				graph1->adjacencyMatrix[i][j] = INF;
			} 
        }
    }
    
}

//换乘路线图同线录入 
void addchange(Graph* graph2, int numNodes){
	int i,j;
	for(i = 0; i < 6; i++){
		for(j = i+1; j < 6; j++){
			graph2->adjacencyMatrix[i][j]=1;
			graph2->adjacencyMatrix[j][i]=1;
		}
		
	}

	for(i = 6; i < 12; i++){
		for(j = i+1; j < 12; j++){
			graph2->adjacencyMatrix[i][j]=1;
			graph2->adjacencyMatrix[j][i]=1;
		}
	}
	
	for(i = 12; i < 18; i++){
		for(j = i+1; j < 18; j++){
			graph2->adjacencyMatrix[i][j]=1;
			graph2->adjacencyMatrix[j][i]=1;
		}
	}
	
	for(i = 18; i < 24; i++){
		for(j = i+1; j < 24; j++){
			graph2->adjacencyMatrix[i][j]=1;
			graph2->adjacencyMatrix[j][i]=1;
		}
	}
	
	for(i = 24; i < 30; i++){
		for(j = i+1; j < 30; j++){
			graph2->adjacencyMatrix[i][j]=1;
			graph2->adjacencyMatrix[j][i]=1;
		}
	}
	
	i=0; 
	for(j = 12; j < 18; j++){
		graph2->adjacencyMatrix[i][j]=1;
		graph2->adjacencyMatrix[j][i]=1;
	}
	
	i=2; 
	for(j = 18; j < 24; j++){
		graph2->adjacencyMatrix[i][j]=1;
		graph2->adjacencyMatrix[j][i]=1;
	}
	
	i=4;
	for(j = 6; j < 12; j++){
		graph2->adjacencyMatrix[i][j]=1;
		graph2->adjacencyMatrix[j][i]=1;
	}

	i=5;
	for(j = 24; j < 30; j++){
		graph2->adjacencyMatrix[i][j]=1;
		graph2->adjacencyMatrix[j][i]=1;
	}
		
} 

// 添加边
void addEdge(Graph* graph, int src, int dest, int weight) {
    graph->adjacencyMatrix[src][dest] = weight;
    graph->adjacencyMatrix[dest][src] = weight;
}

// Dijkstra算法
void dijkstra(Graph* graph, int startNode, int* distance, int* prevNode) {
    bool visited[MAX_NODES] = { false };

    // 初始化距离数组和前驱节点数组
    for (int i = 0; i < graph->numNodes; i++) {
        distance[i] = INF;
        prevNode[i] = -1;
    }

    distance[startNode] = 0;

    for (int i = 0; i < graph->numNodes - 1; i++) {
        // 找到距离最小的节点
        int minDistance = INF;
        int minNode = -1;
        for (int j = 0; j < graph->numNodes; j++) {
            if (!visited[j] && distance[j] < minDistance) {
                minDistance = distance[j];
                minNode = j;
            }
        }

        visited[minNode] = true;

        // 更新与当前节点相邻的节点的距离
        for (int j = 0; j < graph->numNodes; j++) {
            if (!visited[j] && graph->adjacencyMatrix[minNode][j] != INF) {
                int newDistance = distance[minNode] + graph->adjacencyMatrix[minNode][j];
                if (newDistance < distance[j]) {
                    distance[j] = newDistance;
                    prevNode[j] = minNode;
                }
            }
        }
    }
}

// 输出用时最少路径
void printShortimePath(Graph* graph, int startNode, int endNode, int* distance, int* prevNode) {
    if(endNode>30||startNode>30){
    	printf("查询输入出错！\n");
		return; 
	}
    
	int i = endNode; 
    if (i != startNode) {
       if (prevNode[i] == -1) {
            printf("到达目的地%d的用时最少路径不存在\n", i);
        } else {
            int path[MAX_NODES];
            int count = 0;
            int currentNode = i;
            while (currentNode != -1) {
                path[count++] = currentNode;
                currentNode = prevNode[currentNode];
        		}

            printf("到达目的地%d的用时最少路径为：", i);
        	for (int j = count - 1; j >= 0; j--) {
                printf("%d ", path[j]);
            }
            printf("，最短时间为：%d分钟\n", distance[i]);
        }
    }else{
    	printf("起始和终点站一致！\n");
	}
    
}

// 输出最短路径
void printShortestPath(Graph* graph, int startNode, int endNode, int* distance, int* prevNode) {
    if(endNode>30||startNode>30){
    	printf("查询输入出错！\n");
		return; 
	}
    
	int i = endNode; 
    if (i != startNode) {
       if (prevNode[i] == -1) {
            printf("到达目的地%d的最短路径不存在\n", i);
        } else {
            int path[MAX_NODES];
            int count = 0;
            int currentNode = i;
            while (currentNode != -1) {
                path[count++] = currentNode;
                currentNode = prevNode[currentNode];
        		}

            printf("到达目的地%d的最短路径为：", i);
        	for (int j = count - 1; j >= 0; j--) {
                printf("%d ", path[j]);
            }
            printf("\n");
        }
    }
    else{
    	printf("起始和终点站一致！\n");
	} 
    
}

// 输出最少换乘路线 
void printShorchangePath(Graph* graph, int startNode, int endNode, int* distance, int* prevNode) {
    if(endNode>30||startNode>30){
    	printf("查询输入出错！\n");
		return; 
	}
    
	int i = endNode;
	int min = 0; 
    if (i != startNode) {
       if (prevNode[i] == -1) {
            printf("路径不存在！\n", i);
        } else {
            int path[MAX_NODES];
            int count = 0;
            int currentNode = i;
            while (currentNode != -1) {
                path[count++] = currentNode;
                currentNode = prevNode[currentNode];
        		}

            printf("换乘路线为为：", i);
        	for (int j = count - 1; j >= 0; j--) {
                printf("%d ", path[j]);
                min++;
            }
            printf("换乘次数为%d次\n", min-2);
        }
    }
    else{
    	printf("起始和终点站一致！\n");
	} 
    
}

int main() {
    Graph graph;	//求用时最少路径图
	Graph graph1;	//求节点最少路径图 
	Graph graph2;	//求换乘最少路径图 
    int numNodes = 30;
    initGraph(&graph, numNodes);
	
    // 添加边
    addEdge(&graph, 0, 1, 78);
    addEdge(&graph, 1, 2, 207);
    addEdge(&graph, 2, 3, 125);
    addEdge(&graph, 3, 4, 82);
    addEdge(&graph, 4, 5, 480);
    
    
    addEdge(&graph, 6, 7, 153);
    addEdge(&graph, 7, 4, 230);
    addEdge(&graph, 4, 8, 99);
    addEdge(&graph, 8, 9, 139);
    addEdge(&graph, 9, 10, 39);
    addEdge(&graph, 10, 11, 63);
    
    addEdge(&graph, 12, 13, 89);
    addEdge(&graph, 13, 14, 64);
    addEdge(&graph, 14, 0, 28);
    addEdge(&graph, 0, 15, 59);
    addEdge(&graph, 15, 16, 46);
    addEdge(&graph, 16, 17, 94);
    
    addEdge(&graph, 18, 19, 184);
    addEdge(&graph, 19, 20, 273);
    addEdge(&graph, 20, 2, 104);
    addEdge(&graph, 2, 21, 185);
    addEdge(&graph, 21, 22, 43);
    addEdge(&graph, 22, 23, 40);
    
    addEdge(&graph, 24, 25, 34);
    addEdge(&graph, 25, 26, 86);
    addEdge(&graph, 26, 27, 38);
    addEdge(&graph, 27, 28, 30);
    addEdge(&graph, 28, 29, 20);
    addEdge(&graph, 29, 5, 18);
	initGraph1(&graph, &graph1, numNodes);
	initGraph(&graph2, numNodes);
	addchange(&graph2, numNodes);
	
	printf("路线1：0为北京，1为石家庄，2为郑州，3为武汉，4为长沙，5为广州\n");
	printf("路线2：6为昆明，7为贵阳，4为长沙，8为南昌，9为义乌，10杭州，11为上海\n");
	printf("路线3：12为呼和浩特，13为张家口，14为昌平，0为北京，15为承德，16为朝阳，17为沈阳\n");
	printf("路线4：18为兰州，19为西安，20为洛阳，2为郑州，21为徐州，22为东海，23为连云港\n");
	printf("路线5：24为崇左，25为南宁，26为梧州，27为云浮，28为肇庆，29为佛山，5为广州\n");
	int distance[MAX_NODES];
    int prevNode[MAX_NODES]; 
    
    int choice,i,j;
    while(1){
    	printf("请选择你的操作：\n"); 
		printf("1：查询最少换乘次数\n"); 
		printf("2：查询最短路径\n");
		printf("3：查询最短时间\n");
		printf("0：退出系统\n");
		scanf("%d",&choice);
		switch(choice){
			case 1:
				printf("请输入查询的起始站位置下标：");
				scanf("%d",&i);
				printf("请输入查询的终点站位置下标：");
				scanf("%d",&j);
				dijkstra(&graph2, i, distance, prevNode);
				printShorchangePath(&graph2, i, j, distance, prevNode);
				break;
			case 2:
				printf("请输入查询的起始站位置下标：");
				scanf("%d",&i);
				printf("请输入查询的终点站位置下标：");
				scanf("%d",&j);
				dijkstra(&graph1, i, distance, prevNode);
				printShortestPath(&graph1, i, j, distance, prevNode);
				break;
			case 3:
				printf("请输入查询的起始站位置下标：");
				scanf("%d",&i);
				printf("请输入查询的终点站位置下标：");
				scanf("%d",&j);
				dijkstra(&graph, i, distance, prevNode);
				printShortimePath(&graph, i, j, distance, prevNode);
				break;
			case 0:
				exit(0);
			default:
				printf("无效输入！\n");
				break;	 
		}
	}
    return 0;
}
